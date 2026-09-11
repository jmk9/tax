"""종합소득세 신고기간 계산.

신고 시작일: 5월 1일 (소득세법 제70조).
신고 마감일: 5월 31일. 단 국세기본법 제5조에 따라 마감일이
토요일·일요일·공휴일이면 다음 영업일로 순연된다.

공휴일 데이터 우선순위:
1. 공공데이터포털 특일정보 API (환경변수 DATA_GO_KR_KEY 설정 시)
2. 내장 공휴일 테이블 (5~6월분, 2025~2028)
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import date, timedelta

# 5~6월 공휴일만 필요 (마감일 순연 판정 범위).
# 부처님오신날(음력 4/8)·대체공휴일·현충일·선거일 포함.
KNOWN_HOLIDAYS = {
    2025: {date(2025, 5, 5), date(2025, 5, 6), date(2025, 6, 3), date(2025, 6, 6)},
    2026: {date(2026, 5, 5), date(2026, 5, 24), date(2026, 5, 25),
           date(2026, 6, 3), date(2026, 6, 6)},
    2027: {date(2027, 5, 5), date(2027, 5, 13), date(2027, 6, 6)},
    2028: {date(2028, 5, 2), date(2028, 5, 5), date(2028, 6, 6)},
}

API_URL = "https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"


def _fetch_holidays_api(year: int, month: int, service_key: str) -> set:
    params = urllib.parse.urlencode({
        "serviceKey": service_key,
        "solYear": year,
        "solMonth": f"{month:02d}",
        "_type": "json",
        "numOfRows": 50,
    })
    with urllib.request.urlopen(f"{API_URL}?{params}", timeout=10) as resp:
        data = json.loads(resp.read())
    items = data["response"]["body"]["items"]
    if not items:
        return set()
    rows = items["item"]
    if isinstance(rows, dict):
        rows = [rows]
    result = set()
    for row in rows:
        if row.get("isHoliday") == "Y":
            s = str(row["locdate"])
            result.add(date(int(s[:4]), int(s[4:6]), int(s[6:8])))
    return result


def get_holidays(year: int) -> set:
    """해당 연도 5~6월 공휴일 집합."""
    key = os.environ.get("DATA_GO_KR_KEY")
    if key:
        try:
            return _fetch_holidays_api(year, 5, key) | _fetch_holidays_api(year, 6, key)
        except Exception:
            pass  # API 실패 시 내장 테이블로 폴백
    return KNOWN_HOLIDAYS.get(year, set())


def filing_period(filing_year: int, holidays: set = None):
    """(신고 시작일, 신고 마감일) 반환. filing_year는 신고하는 해(귀속연도+1)."""
    if holidays is None:
        holidays = get_holidays(filing_year)
    start = date(filing_year, 5, 1)
    end = date(filing_year, 5, 31)
    while end.weekday() >= 5 or end in holidays:
        end += timedelta(days=1)
    return start, end
