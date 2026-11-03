# GitHub 指标

完全由 GitHub Actions 执行，无需本机或 Codex 在线。
每天北京时间 09:17 采集，周一保存周报；GitHub 调度可能延迟。
公开仓库的标准 GitHub 托管 runner 免费。

查看报告：https://github.com/jiaqianjing/ComfyUI-MidjourneyHub/blob/metrics/latest.md

历史快照和周报保存在 metrics 分支，随公开仓库公开。
Actions 每次运行 Summary 也有报告。手动 Run workflow 会立即采集并保存周报。

默认无需密钥，记录 Stars、Forks、订阅数；增长需积累历史快照。
要启用访问量、克隆量及来源，创建仅授权此仓库的 fine-grained PAT，
Repository permissions 设置 Administration: Read-only，
保存为仓库 Actions secret `METRICS_TOKEN`。默认 GITHUB_TOKEN 没有流量读取权限。
Token 到期需更换，不要复制本机广泛授权的 token。

按 UTC 完整日统计；缺失不填零。每日独立数之和不是周去重人数，克隆不等于用户。
Star/Fork 净增长为边界日期快照差。来源、热门页面是滚动 14 天数据。
接口失败会导致工作流失败，不保存半份快照。
公开仓库长期无活动时 GitHub 可能暂停定时任务，可在 Actions 重新启用。

验证：`python3 -m unittest discover -s tests -p 'test_github_metrics.py'`

官方说明：
- https://docs.github.com/en/rest/metrics/traffic
- https://docs.github.com/en/actions/concepts/billing-and-usage

README 看板包含 30 天访问/克隆折线、当前 Star 的加星日期累计曲线、14 天来源条形图。
Star 时间戳分页采集，仅保存日期，不保存用户身份；已取消的 Star 无法从当前列表重建。
图表由标准库生成 SVG，随每日任务更新 summary.svg，无需外部图表服务。
