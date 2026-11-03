"""README metrics card renderer.

CALLING SPEC: render_card(snapshots, end: date) -> SVG string.
Pure function; no I/O. Uses the same complete UTC days as the weekly report.
"""

from datetime import timedelta
from html import escape

from report import change, total, traffic_days


def render_card(snapshots, end):
    latest = max(snapshots, key=lambda item: item["collected_at"])
    lines = ["GitHub 项目关注度", "更新：" + latest["collected_at"][:10] + " UTC",
             "{} Stars   ·   {} Forks   ·   {} 订阅者".format(
                 latest["counts"]["stars"], latest["counts"]["forks"],
                 latest["counts"]["subscribers"]),
             "最近 7 个完整日：{} 至 {}".format(end - timedelta(days=7), end - timedelta(days=1))]
    for metric, label in (("views", "访问"), ("clones", "克隆")):
        days = traffic_days(snapshots, metric)
        current, _ = total(days, end - timedelta(days=7), "count")
        previous, _ = total(days, end - timedelta(days=14), "count")
        value = "数据不足" if current is None else str(current) + " 次"
        lines.append("{}：{}    较前 7 天：{}".format(label, value, change(previous, current)))
    lines.append("克隆量不等于用户数 · 完整趋势见下方报告")
    text = []
    for index, line in enumerate(lines):
        size = 24 if index == 0 else 16
        text.append('<text x="24" y="{}" font-size="{}">{}</text>'.format(
            38 + index * 34, size, escape(line)))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="760" height="280" '
            'viewBox="0 0 760 280" role="img" aria-labelledby="title">'
            '<title id="title">GitHub 项目关注度：最近七天访问和克隆趋势</title>'
            '<rect width="760" height="280" rx="12" fill="#f6f8fa"/>'
            '<g fill="#1f2328" font-family="sans-serif">' + ''.join(text) + '</g></svg>\n')
