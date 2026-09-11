"""Trigger A~D 판정.

원 스펙 대비 수정:
- `today ==` 정확일치 대신 창(window) + notified 플래그: 하루 놓쳐도 다음 실행에서 발송.
- Trigger D에 late_filing_notified 조건 추가 (중복 발송 방지).
- 발송 여부 플래그는 state, 알림 on/off는 config로 분리.
"""
from datetime import date, timedelta

DONE_STATUSES = {"completed", "not_applicable"}


def evaluate(today: date, start: date, end: date, state: dict, prefs: dict) -> list:
    """발송할 trigger 이름 목록 반환. state는 변경하지 않는다."""
    if state["status"] in DONE_STATUSES:
        return []

    fired = []
    if (prefs.get("filing_open", True)
            and start <= today <= end
            and not state["filing_open_notified"]):
        fired.append("filing_open")

    if (prefs.get("deadline_7_days", True)
            and end - timedelta(days=7) <= today <= end
            and not state["d7_notified"]):
        fired.append("d7")

    if (prefs.get("deadline_1_day", True)
            and end - timedelta(days=1) <= today <= end
            and not state["d1_notified"]):
        fired.append("d1")

    if (prefs.get("late_filing_check", True)
            and today > end
            and not state["late_filing_notified"]):
        fired.append("late_filing")

    return fired


NOTIFIED_FLAG = {
    "filing_open": "filing_open_notified",
    "d7": "d7_notified",
    "d1": "d1_notified",
    "late_filing": "late_filing_notified",
}


def mark_notified(state: dict, trigger: str) -> None:
    state[NOTIFIED_FLAG[trigger]] = True
