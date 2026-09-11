"""연도별 신고 state 관리. state/{filing_year}.json 에 저장."""
import json
from datetime import datetime, timezone
from pathlib import Path

VALID_STATUSES = {"not_started", "checking", "completed", "not_applicable"}


def default_state(filing_year: int) -> dict:
    return {
        "tax_year": filing_year - 1,
        "filing_year": filing_year,
        "status": "not_started",
        "filing_open_notified": False,
        "d7_notified": False,
        "d1_notified": False,
        "late_filing_notified": False,
        "completed_at": None,
    }


class StateStore:
    def __init__(self, state_dir):
        self.state_dir = Path(state_dir)

    def _path(self, filing_year: int) -> Path:
        return self.state_dir / f"{filing_year}.json"

    def load(self, filing_year: int) -> dict:
        """state 로드. 없으면 새로 생성 (연도 자동 전환)."""
        p = self._path(filing_year)
        if p.exists():
            return json.loads(p.read_text())
        return default_state(filing_year)

    def save(self, state: dict) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        p = self._path(state["filing_year"])
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2))

    def mark_completed(self, filing_year: int) -> dict:
        state = self.load(filing_year)
        state["status"] = "completed"
        state["completed_at"] = datetime.now(timezone.utc).isoformat()
        self.save(state)
        return state
