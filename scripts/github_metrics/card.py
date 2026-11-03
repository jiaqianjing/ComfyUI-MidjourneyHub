"""README dashboard renderer.

CALLING SPEC: render_card(snapshots, end: date) -> standalone SVG string.
Pure function; uses complete UTC days, retains gaps, no network or file I/O.
"""
from collections import Counter
from datetime import date, timedelta

from charts import box, line_chart, text
from report import total, traffic_days


def render_card(snapshots, end):
    latest = max(snapshots, key=lambda item: item['collected_at'])
    counts = latest['counts']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="860" viewBox="0 0 1000 860" role="img" aria-labelledby="title desc">',
             '<title id="title">MidjourneyHub activity dashboard</title>',
             '<desc id="desc">Stars, daily views and clones, star timeline and top traffic sources. Missing observations remain gaps.</desc>',
             '<rect width="1000" height="860" rx="22" fill="#090f1d"/>',
             '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">',
             text(32, 36, 'MIDJOURNEYHUB / OPEN SOURCE PULSE', 12, '#5eead4', 600),
             text(32, 78, 'Project activity, at a glance.', 30, '#f1f5f9', 700),
             text(32, 105, 'Repository activity, collected daily on GitHub Actions', 14),
             text(746, 36, 'UPDATED ' + latest['collected_at'][:10] + ' UTC', 11)]
    values = [('STARS', counts['stars'], 'Current community', '#fbbf24'),
              ('FORKS', counts['forks'], 'Projects branching out', '#a78bfa')]
    for metric, label, color in [('views', 'VIEWS / 7 DAYS', '#2dd4bf'), ('clones', 'CLONES / 7 DAYS', '#60a5fa')]:
        days = traffic_days(snapshots, metric)
        current, _ = total(days, end - timedelta(days=7), 'count')
        previous, _ = total(days, end - timedelta(days=14), 'count')
        delta = 'Awaiting baseline' if current is None or previous is None else (
            'No change' if current == previous else f'{current-previous:+d} vs previous 7d')
        values.append((label, current if current is not None else '—', delta, color))
    for i, (label, value, detail, color) in enumerate(values):
        x = 32 + i * 240
        parts += [box(x, 130, 216, 116), text(x+18, 155, label, 11),
                  text(x+18, 199, value, 36, color, 700), text(x+18, 227, detail, 12)]
    for i, (metric, title, color) in enumerate([('views', 'Repository views', '#2dd4bf'), ('clones', 'Repository clones', '#60a5fa')]):
        x = 32 + i * 480
        days = traffic_days(snapshots, metric)
        dates = [end - timedelta(days=30-j) for j in range(30)]
        points = [(j, days[str(day)]['count'] if str(day) in days else None) for j, day in enumerate(dates)]
        coverage = sum(value is not None for _, value in points)
        parts += [box(x, 266, 456, 260), text(x+20, 296, title, 18, '#f1f5f9', 600),
                  text(x+20, 318, f'30-day window · {coverage} observed days · gaps = unavailable', 11),
                  line_chart(points, x+52, 340, 378, 140, color, (str(dates[0])[5:], str(dates[-1])[5:]))]
    parts += [box(32, 546, 456, 260), text(52, 576, 'The star timeline', 18, '#f1f5f9', 600),
              text(52, 598, 'Current stargazers by date starred · unstars not reconstructed', 10)]
    history = latest.get('star_dates', [])
    if history:
        daily = Counter(item[:10] for item in history)
        first = date.fromisoformat(min(daily))
        points, running = [(0, 0)], 0
        for day, count in sorted(daily.items()):
            running += count
            points.append(((date.fromisoformat(day)-first).days, running))
        points.append(((end-first).days, running))
        parts.append(line_chart(points, 84, 620, 378, 140, '#fbbf24', (str(first), str(end)), step=True))
    else:
        parts.append(text(52, 690, 'Star history not available yet', 14))
    parts += [box(512, 546, 456, 260), text(532, 576, 'Where discovery starts', 18, '#f1f5f9', 600),
              text(532, 598, 'Top referrers · GitHub rolling 14-day window', 11)]
    rows = sorted(latest['traffic'].get('popular/referrers', []), key=lambda row: row['count'], reverse=True)[:4]
    maximum = max([row['count'] for row in rows] + [1])
    for i, row in enumerate(rows):
        yy = 626 + i * 42
        name = row['referrer']
        name = name if len(name) <= 38 else name[:35] + '…'
        parts += [text(532, yy, name, 12, '#cbd5e1'), text(920, yy, row['count'], 12, '#a78bfa'),
                  f'<rect x="532" y="{yy+8}" width="410" height="6" rx="3" fill="#24324a"/>',
                  f'<rect x="532" y="{yy+8}" width="{410*row["count"]/maximum:.1f}" height="6" rx="3" fill="#a78bfa"/>']
    if not rows:
        parts.append(text(532, 670, 'No referral data returned by GitHub', 14))
    parts += [text(32, 836, 'UTC calendar days · Clones are not active users · Click for the full weekly report', 12), '</g></svg>\n']
    return ''.join(parts)
