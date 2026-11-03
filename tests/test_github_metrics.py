"""CALLING SPEC: unittest discovery; tests pure metrics and local storage contracts.
Side effects: temporary files only; no GitHub calls.
"""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/github_metrics"))
from report import change, total, traffic_days
from storage import read_snapshots, save_json


class MetricsTests(unittest.TestCase):
    def test_latest_complete_observation_wins(self):
        def snapshot(collected, count):
            return {"collected_at": collected, "traffic": {"views": {"views": [
                {"timestamp": "2026-11-01T00:00:00Z", "count": count, "uniques": 1}]}}}
        partial = snapshot("2026-11-01T08:00:00Z", 2)
        first = snapshot("2026-11-02T08:00:00Z", 4)
        revised = snapshot("2026-11-03T08:00:00Z", 6)
        self.assertEqual(traffic_days([partial], "views"), {})
        self.assertEqual(traffic_days([revised, first], "views")["2026-11-01"]["count"], 6)

    def test_missing_is_not_zero(self):
        self.assertEqual(total({}, date(2026, 11, 1), "count"), (None, 0))
        days = {"2026-11-{:02d}".format(i): {"count": 0} for i in range(1, 8)}
        self.assertEqual(total(days, date(2026, 11, 1), "count"), (0, 7))

    def test_zero_baseline(self):
        self.assertEqual(change(0, 2), "从 0 增至 2")
        self.assertEqual(change(None, 2), "数据不足")
        self.assertEqual(change(10, 5), "-50.0%")

    def test_atomic_storage_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "snapshots/test.json"
            save_json(path, {"value": 1})
            save_json(path, {"value": 2})
            self.assertEqual(read_snapshots(root), [{"value": 2}])


if __name__ == "__main__":
    unittest.main()
