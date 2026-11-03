"""CALLING SPEC: unittest discovery; SVG data accuracy tests, no external I/O."""
import sys
import unittest
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/github_metrics'))
from charts import line_chart
from card import render_card


class DashboardTests(unittest.TestCase):
    def test_gaps_do_not_become_lines_or_zeroes(self):
        svg = line_chart([(0, 3), (1, None), (2, 4)], 0, 0, 100, 100, '#fff', ('a', 'b'))
        self.assertEqual(svg.count('stroke-width="2.5"'), 2)
        self.assertEqual(svg.count('<circle'), 2)

    def test_missing_data_is_explicit(self):
        snapshot = {'collected_at': '2026-11-03T09:00:00Z',
                    'counts': {'stars': 0, 'forks': 0}, 'traffic': {}}
        svg = render_card([snapshot], date(2026, 11, 3))
        ET.fromstring(svg)
        self.assertIn('暂无数据', svg)
        self.assertIn('等待流量数据', svg)

    def test_partial_totals_are_not_presented_as_full_month(self):
        from card import total_label, window_series
        snapshot = {'collected_at': '2026-11-03T09:00:00Z', 'traffic': {
            'views': {'views': [{'timestamp': '2026-11-02T00:00:00Z', 'count': 5}]}}}
        points = window_series([snapshot], 'views', date(2026, 11, 3))
        self.assertEqual(len(points), 30)
        self.assertEqual(total_label(points), '5（已采集 1/30 天）')
        self.assertEqual(total_label([(i, 0) for i in range(30)]), '0')
