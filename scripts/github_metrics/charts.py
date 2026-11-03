"""Pure SVG chart primitives.

CALLING SPEC: text/box/line_chart -> SVG fragments; points use numeric x and
nonnegative y, or None for missing observations. No side effects.
"""
from html import escape


def text(x, y, value, size=14, color='#94a3b8', weight=400):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}">{escape(str(value))}</text>')


def box(x, y, width, height):
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            'rx="16" fill="#111c30" stroke="#24324a"/>')


def line_chart(points, x, y, width, height, color, labels, step=False):
    known = [(a, b) for a, b in points if b is not None]
    if not known:
        return text(x + 16, y + height / 2, 'Awaiting observations', 15)
    left, right = min(a for a, _ in points), max(a for a, _ in points)
    maximum = max(1, max(b for _, b in known))
    def project(a, b):
        return x + (a - left) / max(1, right - left) * width, y + height - b / maximum * height
    parts = []
    for ratio in (0, .5, 1):
        yy = y + height - ratio * height
        parts.append(f'<path d="M{x} {yy}h{width}" stroke="#26334b" stroke-dasharray="3 5"/>')
        parts.append(text(x - 30, yy + 4, f'{maximum * ratio:g}', 11))
    segments, segment = [], []
    for a, b in points:
        if b is None:
            if segment:
                segments.append(segment)
            segment = []
        else:
            segment.append(project(a, b))
    if segment:
        segments.append(segment)
    for segment in segments:
        path = f'M{segment[0][0]:.2f} {segment[0][1]:.2f}'
        for xx, yy in segment[1:]:
            path += f' H{xx:.2f} V{yy:.2f}' if step else f' L{xx:.2f} {yy:.2f}'
        parts.append(f'<path d="{path} L{segment[-1][0]:.2f} {y+height} L{segment[0][0]:.2f} {y+height} Z" fill="{color}" opacity=".09"/>')
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>')
        for xx, yy in segment:
            parts.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="2.5" fill="{color}"/>')
    parts += [text(x, y + height + 22, labels[0], 11),
              text(x + width - 72, y + height + 22, labels[1], 11)]
    return ''.join(parts)
