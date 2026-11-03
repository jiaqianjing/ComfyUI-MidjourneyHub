"""Compact README activity summary.

CALLING SPEC: render_card(snapshots, end: date) -> standalone SVG string.
Pure function; 30 complete UTC days, missing observations remain gaps.
Partial totals explicitly show observed-day coverage; no I/O.
"""
from datetime import timedelta

from charts import line_chart, text
from report import traffic_days


def window_series(snapshots, metric, end):
    """Return 30 (day index, count or None) pairs without filling missing days."""
    days = traffic_days(snapshots, metric)
    dates = [end - timedelta(days=30-i) for i in range(30)]
    return [(i, days[str(day)]['count'] if str(day) in days else None)
            for i, day in enumerate(dates)]


def total_label(points):
    """Return a complete 30-day total or explicitly labeled partial observation."""
    known = [value for _, value in points if value is not None]
    if not known:
        return '暂无数据'
    value = str(sum(known))
    return value if len(known) == 30 else f'{value}（已采集 {len(known)}/30 天）'


def render_card(snapshots, end):
    latest = max(snapshots, key=lambda item: item['collected_at'])
    counts = latest['counts']
    views = window_series(snapshots, 'views', end)
    clones = window_series(snapshots, 'clones', end)
    maximum = max([value for _, value in views + clones if value is not None] + [2])
    maximum += maximum % 2
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="310" viewBox="0 0 900 310" role="img" aria-labelledby="title desc">',
             '<title id="title">项目近 30 天访问与克隆趋势</title>',
             '<desc id="desc">访问与克隆使用同一坐标轴。未采集日期留空，部分合计标注采集天数。</desc>',
             '<rect x=".5" y=".5" width="899" height="309" rx="6" fill="#ffffff" stroke="#d0d7de"/>',
             '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Noto Sans CJK SC,sans-serif">',
             text(24, 33, f'Stars {counts["stars"]}   ·   Forks {counts["forks"]}   ·   近 30 天访问 {total_label(views)}   ·   克隆 {total_label(clones)}', 15, '#24292f', 600),
             text(24, 62, '每日次数 · 最近 30 个完整日', 12),
             text(652, 62, '更新 ' + latest['collected_at'][:10] + ' UTC', 12),
             '<path d="M620 87h20" stroke="#0969da" stroke-width="2.5"/>', text(648, 91, '访问', 12),
             '<path d="M708 87h20" stroke="#6e7781" stroke-width="2.5"/>', text(736, 91, '克隆', 12)]
    labels = (str(end-timedelta(days=30))[5:], str(end-timedelta(days=1))[5:])
    for points, color, axes in ((views, '#0969da', True), (clones, '#6e7781', False)):
        if any(value is not None for _, value in points):
            parts.append(line_chart(points, 62, 108, 802, 136, color, labels,
                                    maximum=maximum, axes=axes or not any(v is not None for _, v in views)))
    if not any(value is not None for _, value in views + clones):
        parts.append(text(62, 176, '等待流量数据', 14))
    parts += [text(24, 292, '未采集日期留空；克隆量不代表安装量或活跃用户数。', 11), '</g></svg>\n']
    return ''.join(parts)
