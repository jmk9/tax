from tax_agent.state import StateStore, default_state


def test_load_creates_default_for_new_year(tmp_path):
    store = StateStore(tmp_path)
    st = store.load(2027)
    assert st["filing_year"] == 2027
    assert st["tax_year"] == 2026
    assert st["status"] == "not_started"


def test_save_load_roundtrip(tmp_path):
    store = StateStore(tmp_path)
    st = default_state(2026)
    st["filing_open_notified"] = True
    store.save(st)
    loaded = store.load(2026)
    assert loaded == st


def test_mark_completed(tmp_path):
    store = StateStore(tmp_path)
    st = store.mark_completed(2026)
    assert st["status"] == "completed"
    assert st["completed_at"] is not None
    assert store.load(2026)["status"] == "completed"


def test_years_are_independent(tmp_path):
    store = StateStore(tmp_path)
    store.mark_completed(2026)
    assert store.load(2027)["status"] == "not_started"
