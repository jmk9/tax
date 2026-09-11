from datetime import date

from tax_agent.tax_calendar import filing_period, KNOWN_HOLIDAYS


def test_2025_deadline_rolls_to_june_2():
    # 2025-05-31 토요일, 6/1 일요일 -> 6/2 월요일
    start, end = filing_period(2025, KNOWN_HOLIDAYS[2025])
    assert start == date(2025, 5, 1)
    assert end == date(2025, 6, 2)


def test_2026_deadline_rolls_to_june_1():
    # 2026-05-31 일요일 -> 6/1 월요일 (스펙 예시)
    _, end = filing_period(2026, KNOWN_HOLIDAYS[2026])
    assert end == date(2026, 6, 1)


def test_2027_deadline_stays_may_31():
    # 2027-05-31 월요일, 공휴일 아님
    _, end = filing_period(2027, KNOWN_HOLIDAYS[2027])
    assert end == date(2027, 5, 31)


def test_holiday_on_rolled_date_rolls_again():
    # 5/31이 토요일이고 다음 월요일이 공휴일인 가상 케이스
    holidays = {date(2025, 6, 2)}
    _, end = filing_period(2025, holidays)
    assert end == date(2025, 6, 3)


def test_unknown_year_weekend_only_fallback():
    # 내장 테이블에 없는 연도: 주말 순연만 적용
    _, end = filing_period(2030, set())
    # 2030-05-31 금요일
    assert end == date(2030, 5, 31)
