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

    def test_empty_data_and_xml_escaping(self):
        snapshot = {'collected_at': '2026-11-03T09:00:00Z',
                    'counts': {'stars': 0, 'forks': 0},
                    'traffic': {'popular/referrers': [{'referrer': 'A&B <test>', 'count': 1}]}}
        svg = render_card([snapshot], date(2026, 11, 3))
        ET.fromstring(svg)
        self.assertIn('A&amp;B &lt;test&gt;', svg)
        self.assertIn('0 observed days', svg)
        self.assertIn('Awaiting baseline', svg)

    def test_single_day_stars_render(self):
        snapshot = {'collected_at': '2026-11-03T09:00:00Z',
                    'counts': {'stars': 2, 'forks': 0}, 'traffic': {},
                    'star_dates': ['2026-11-03T01:00:00Z', '2026-11-03T02:00:00Z']}
        svg = render_card([snapshot], date(2026, 11, 3))
        ET.fromstring(svg)
        self.assertNotIn('Star history not available yet', svg)
