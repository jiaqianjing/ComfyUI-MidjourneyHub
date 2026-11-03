"""Pure weekly trend calculations.

CALLING SPEC: render(snapshots, end: date) -> Markdown str.
Windows: [end-7, end) versus [end-14, end-7), UTC calendar days.
Side effects: none. Missing data is unknown, never silently zero-filled.
"""

from datetime import date, timedelta


def traffic_days(snapshots, metric):
    days = {}
    for snapshot in sorted(snapshots, key=lambda item: item["collected_at"]):
        collected = snapshot["collected_at"][:10]
        for row in snapshot["traffic"].get(metric, {}).get(metric, []):
            day = row["timestamp"][:10]
            # Exclude partial collection-day observations. Later snapshots revise days.
            if day < collected:
                days[day] = row
    return days


def total(days, start, field):
    keys = [(start + timedelta(days=i)).isoformat() for i in range(7)]
    present = [key for key in keys if key in days]
    if len(present) != 7:
        return None, len(present)
    return sum(days[key][field] for key in keys), 7


def change(before, after):
    if before is None or after is None:
        return "数据不足"
    if before == 0:
        return "持平" if after == 0 else "从 0 增至 {}".format(after)
    return "{:+.1f}%".format((after - before) / before * 100)


def display(result):
    value, coverage = result
    return str(value) if value is not None else "数据不足（{}/7 天）".format(coverage)


def render(snapshots, end):
    recent = end - timedelta(days=7)
    previous = end - timedelta(days=14)
    lines = ["# GitHub 每周关注度报告", "",
             "统计按 UTC 日界线；结束日期不含当天。",
             "本期：{} 至 {}；上期：{} 至 {}。".format(
                 recent, end - timedelta(days=1), previous, recent - timedelta(days=1)),
             "", "| 指标 | 上期 | 本期 | 环比 |", "|---|---:|---:|---:|"]
    for metric, label in (("views", "访问"), ("clones", "完整克隆")):
        days = traffic_days(snapshots, metric)
        for field, suffix in (("count", "量"), ("uniques", "每日独立数之和（非周去重）")):
            before = total(days, previous, field)
            after = total(days, recent, field)
            lines.append("| {}{} | {} | {} | {} |".format(
                label, suffix, display(before), display(after), change(before[0], after[0])))
    by_day = {item["collected_at"][:10]: item["counts"] for item in
              sorted(snapshots, key=lambda item: item["collected_at"])}
    for field, label in (("stars", "Star"), ("forks", "Fork"), ("subscribers", "订阅者")):
        def delta(start, finish):
            a, b = by_day.get(str(start)), by_day.get(str(finish))
            return b[field] - a[field] if a is not None and b is not None else None
        a, b = delta(previous, recent), delta(recent, end)
        lines.append("| {} 净增长 | {} | {} | — |".format(
            label, a if a is not None else "等待基线", b if b is not None else "等待基线"))
    lines += ["", "Star/Fork/订阅净增长按边界日期采集时刻的快照差计算，并非精确午夜值。",
              "克隆可能来自自动化，不代表安装或活跃用户。缺失日期不作为零处理。",
              "GitHub 数据可能延迟，后续采集会修订流量日数据。", ""]
    if snapshots:
        latest = max(snapshots, key=lambda item: item["collected_at"])
        lines += ["## 最近一次采集", "", latest["collected_at"], "",
                  "累计：{} Stars · {} Forks · {} 订阅者。".format(
                      latest["counts"]["stars"], latest["counts"]["forks"],
                      latest["counts"]["subscribers"]), "",
                  "来源和热门页面为该快照的滚动 14 天数据，不能归因到单周。", ""]
        for key, field, title in (("popular/referrers", "referrer", "来源网站"),
                                  ("popular/paths", "path", "热门页面")):
            lines += ["### " + title, ""]
            rows = latest["traffic"].get(key, [])
            lines += ["- {}：{} 次，{} 独立访客".format(
                row[field].replace("\n", " "), row["count"], row["uniques"]) for row in rows]
            if not rows:
                lines.append("暂无数据。")
            lines.append("")
    return "\n".join(lines)
