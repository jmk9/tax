"""CLI: run(매일 cron 진입점) / complete / status."""
import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import mailer, state as state_mod, tax_calendar, templates, triggers

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"
DEFAULT_STATE_DIR = Path(__file__).resolve().parent.parent / "state"


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def cmd_run(args):
    cfg = load_config(args.config)
    tz = ZoneInfo(cfg["user"].get("timezone", "Asia/Seoul"))
    today = date.fromisoformat(args.today) if args.today else datetime.now(tz).date()

    filing_year = today.year
    store = state_mod.StateStore(args.state_dir)
    st = store.load(filing_year)  # 없으면 자동 생성 (연도 전환)
    start, end = tax_calendar.filing_period(filing_year)

    fired = triggers.evaluate(today, start, end, st, cfg.get("notification", {}))
    if not fired:
        print(f"[{today}] 발송할 알림 없음 (status={st['status']})")
        store.save(st)
        return

    for trig in fired:
        subject, body = templates.render(
            trig, start=start, end=end,
            filing_year=filing_year, tax_year=st["tax_year"],
        )
        if args.dry_run:
            print(f"--- DRY RUN [{trig}] to={cfg['user']['email']}")
            print(f"Subject: {subject}")
            print(body)
        else:
            mailer.send_email(cfg["smtp"], cfg["user"]["email"], subject, body)
            print(f"[{today}] 발송 완료: {trig}")
        triggers.mark_notified(st, trig)
    store.save(st)


def cmd_complete(args):
    filing_year = args.year or datetime.now(ZoneInfo("Asia/Seoul")).year
    store = state_mod.StateStore(args.state_dir)
    st = store.mark_completed(filing_year)
    print(f"{filing_year}년 신고(귀속 {st['tax_year']}년) completed 처리. 추가 알림 없음.")


def cmd_status(args):
    store = state_mod.StateStore(args.state_dir)
    state_dir = Path(args.state_dir)
    files = sorted(state_dir.glob("*.json")) if state_dir.exists() else []
    if not files:
        print("저장된 state 없음")
        return
    for f in files:
        st = store.load(int(f.stem))
        start, end = tax_calendar.filing_period(st["filing_year"])
        print(f"신고연도 {st['filing_year']} (귀속 {st['tax_year']}) "
              f"기간 {start}~{end} status={st['status']} "
              f"open={st['filing_open_notified']} d7={st['d7_notified']} "
              f"d1={st['d1_notified']} late={st['late_filing_notified']}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="tax-agent",
                                description="종합소득세 신고 알림 에이전트")
    p.add_argument("--config", default=str(DEFAULT_CONFIG))
    p.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    sub = p.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="트리거 확인 후 알림 발송 (cron 진입점)")
    p_run.add_argument("--today", help="테스트용 날짜 (YYYY-MM-DD)")
    p_run.add_argument("--dry-run", action="store_true", help="발송 대신 출력")
    p_run.set_defaults(func=cmd_run)

    p_done = sub.add_parser("complete", help="해당 신고연도 completed 처리")
    p_done.add_argument("year", nargs="?", type=int, help="신고연도 (기본: 올해)")
    p_done.set_defaults(func=cmd_complete)

    p_st = sub.add_parser("status", help="연도별 state 표시")
    p_st.set_defaults(func=cmd_status)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
