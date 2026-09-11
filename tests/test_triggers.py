from datetime import date

from tax_agent.state import default_state
from tax_agent.triggers import evaluate, mark_notified

START = date(2026, 5, 1)
END = date(2026, 6, 1)
PREFS = {"filing_open": True, "deadline_7_days": True,
         "deadline_1_day": True, "late_filing_check": True}


def test_trigger_a_fires_on_start():
    st = default_state(2026)
    assert evaluate(START, START, END, st, PREFS) == ["filing_open"]


def test_trigger_a_fires_once():
    st = default_state(2026)
    mark_notified(st, "filing_open")
    assert evaluate(START, START, END, st, PREFS) == []


def test_trigger_a_catches_up_after_missed_days():
    # 시작일에 안 돌았어도 기간 중이면 발송
    st = default_state(2026)
    assert "filing_open" in evaluate(date(2026, 5, 10), START, END, st, PREFS)


def test_trigger_b_window():
    st = default_state(2026)
    mark_notified(st, "filing_open")
    fired = evaluate(date(2026, 5, 25), START, END, st, PREFS)  # END-7
    assert fired == ["d7"]


def test_trigger_b_catches_up():
    # D-7 당일 못 돌고 D-5에 돌아도 발송
    st = default_state(2026)
    mark_notified(st, "filing_open")
    assert "d7" in evaluate(date(2026, 5, 27), START, END, st, PREFS)


def test_trigger_c_day_before_deadline():
    st = default_state(2026)
    mark_notified(st, "filing_open")
    mark_notified(st, "d7")
    assert evaluate(date(2026, 5, 31), START, END, st, PREFS) == ["d1"]


def test_trigger_d_after_deadline_once():
    st = default_state(2026)
    fired = evaluate(date(2026, 6, 5), START, END, st, PREFS)
    assert fired == ["late_filing"]
    mark_notified(st, "late_filing")
    assert evaluate(date(2026, 6, 6), START, END, st, PREFS) == []


def test_completed_suppresses_everything():
    st = default_state(2026)
    st["status"] = "completed"
    assert evaluate(date(2026, 5, 25), START, END, st, PREFS) == []
    assert evaluate(date(2026, 6, 5), START, END, st, PREFS) == []


def test_not_applicable_suppresses_everything():
    st = default_state(2026)
    st["status"] = "not_applicable"
    assert evaluate(date(2026, 6, 5), START, END, st, PREFS) == []


def test_prefs_disable_trigger():
    st = default_state(2026)
    prefs = dict(PREFS, deadline_7_days=False)
    mark_notified(st, "filing_open")
    assert evaluate(date(2026, 5, 25), START, END, st, prefs) == []


def test_before_period_nothing_fires():
    st = default_state(2026)
    assert evaluate(date(2026, 4, 30), START, END, st, PREFS) == []
