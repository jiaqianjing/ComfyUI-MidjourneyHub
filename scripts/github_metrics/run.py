"""Local metrics orchestration; Python 3.8+, authenticated gh required.

CALLING SPEC: python3 scripts/github_metrics/run.py [--weekly] [--output DIR]
Side effects: read GitHub; archive snapshot; write latest and optional weekly report.
Failure exits nonzero; never pushes data or sends messages.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from api import collect
from card import render_card
from report import render
from storage import read_snapshots, save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weekly", action="store_true")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parents[2] / "metrics")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    snapshot = collect("jiaqianjing/ComfyUI-MidjourneyHub", now)
    root = args.output
    save_json(root / "snapshots" / (now.strftime("%Y-%m-%dT%H%M%S%fZ") + ".json"), snapshot)
    snapshots = read_snapshots(root)
    report = render(snapshots, now.date())
    (root / "summary.svg").write_text(render_card(snapshots, now.date()), encoding="utf-8")
    (root / "latest.md").write_text(report, encoding="utf-8")
    if args.weekly:
        weekly = root / "weekly"
        weekly.mkdir(exist_ok=True)
        (weekly / (now.date().isoformat() + ".md")).write_text(report, encoding="utf-8")
    print("Saved metrics and report: " + str(root / "latest.md"))


if __name__ == "__main__":
    main()
