# 简介
该节点可以在 ComfyUI 中使用各种主流商业模型绘图节点，目前后端是使用**云雾 API** 提供的 API 支持。可以通过这个链接进行注册和使用：[https://www.cocode.icu/](https://www.cocode.icu/)

## 项目概况

[![项目近 30 天访问与克隆趋势](https://raw.githubusercontent.com/jiaqianjing/ComfyUI-MidjourneyHub/metrics/summary.svg)](https://github.com/jiaqianjing/ComfyUI-MidjourneyHub/blob/metrics/latest.md)

[详细报告与流量来源](https://github.com/jiaqianjing/ComfyUI-MidjourneyHub/blob/metrics/latest.md) · [历史周报](https://github.com/jiaqianjing/ComfyUI-MidjourneyHub/tree/metrics/weekly)

每天自动更新，按 UTC 完整日统计。数据不足 30 天时标注已采集天数；访问和克隆仅用于观察项目关注度，不代表广告曝光或实际用户数。

**推广合作**：欢迎模型/API 服务商洽谈赞助与推广合作，可通过 [GitHub Issue](https://github.com/jiaqianjing/ComfyUI-MidjourneyHub/issues/new?title=推广合作) 联系。

## 模型兼容说明

| 节点 | 模型 | 参数说明 |
| --- | --- | --- |
| GPT Image 生成 / 编辑 | 原有 2-all、1.5、1；新增 `gpt-image-2.5-flare`、`gpt-image-2.5-sunburst` | 2.5 可选 `xhigh` / `max` 及更大尺寸；兼容 URL 和 Base64 图片返回 |
| Gemini 生成 / 编辑 | 默认 `gemini-3-pro-image-preview` | 保留 1K / 2K 和原有工作流 |
| Gemini 生成 / 编辑（实验） | `gemini-3.1-flash-lite-image`（Nano Banana 2 Lite） | 仅支持 1K；云雾文档标为“开发中”，账号渠道可能尚未开放 |

模型选择位于节点可选参数中。参数下拉展示全部选项，执行前按模型校验；旧模型选择 2.5 专属质量/尺寸、或 Lite 选择 2K 时，会明确报错，不会静默替换参数。GPT 默认仍为 `gpt-image-2-all`，Gemini 默认仍为 Pro。旧工作流未传 GPT model 时也保留原来的 1.5 行为。

本次适配依据云雾的 [GPT 2.5 生成](https://yunwu.apifox.cn/api-513295251)、[GPT 2.5 编辑](https://yunwu.apifox.cn/api-513297453)、[Gemini Lite](https://yunwu.apifox.cn/api-480926826) 文档。已通过离线请求和响应测试；尚未完成真实出图验证，具体可用性取决于 API Token 分组和渠道。Midjourney 版本列表本次未变更。

## 更新
* 2026.11.03 新增云雾 GPT Image 2.5 生成/编辑适配，以及 Gemini 可选模型和 Nano Banana 2 Lite 实验支持。
* 2026.05.03 更新 openai **[GPT Image Generate]** 和 **[GPT Image Edit]** 节点，新增 `gpt-image-2-all` 模型支持（默认模型）
* 2026.01.22 更新 openai **[GPT Image Edit]** 节点，使用 Openai 最新的绘图模型 `gpt-image-1.5` 
* 2026.01.22 更新 openai **[GPT Image Generate]** 节点，使用 Openai 最新的绘图模型 `gpt-image-1.5` 
* 2026.01.22 新增 Google **[Gemini Image Generate]** 节点，使用 Gemini 3 Pro Image Preview 模型根据提示词生图;
* 2026.01.22 新增 Google **[Gemini Image Edit]** 节点，使用 Gemini 3 Pro Image Preview 模型根据提示词和参考图片进行编辑;
* 2025.06.18 新增 openai **[GPT Image Edit]** 节点，使用 Openai 最新的绘图模型 `gpt-image-1` 根据提示词和待修改的图片进行编辑;
* 2025.06.18 新增 openai **[GPT Image Generate]** 节点，使用 Openai 最新的绘图模型 `gpt-image-1` 根据提示词绘图;
* 2025.06.18 新增 midjourney **[Midjourney Blend (Image Mix)]** 节点，可上传两张图进行融合，支持 `seed` 避免缓存;
* 2024.12.13 引入协程的方式改造原始同步方法，通过并发加快创建图片和同步状态的响应尤其是 [Batch Upsale/Variation] 节点;
* 2024.12.10 支持 midjourney **[Midjourney Batch Upscale/Variation]** 节点;
* 2024.12.06 支持 midjourney **[MidjourneyImagineNode] 和 [Midjourney Upscale/Variation]** 节点;


## 使用方法
### 1. 修改自己的 api_url/api_key
![](./example/config.png)
* [注]：因为后端 API 使用的云雾 API，他们可能不定期修改域名（api_url）

### 2. 工作流示例
1. **MidjourneyImagineNode** 节点 + **Midjourney Upscale/Variation** 节点
![](./example/example.png)

2. **MidjourneyImagineNode** 节点 + **Midjourney Batch Upscale/Variation** 节点
![](./example/example_batch_upscale.png)

3. **Midjourney Blend (Image Mix)** 节点（两张图片融合）
    
    示例1:
    ![](./example/example_mj_blend_01.png)

    示例2:
    ![](./example/example_mj_blend_02.png)

4. **GPT Image Generate** 节点生图（openai 最新的 SOTA 生图模型）
    示例:
    ![](./example/example_gpt_image_generation.png)

5. **GPT Image Edit** 节点编辑图（openai 最新的 SOTA 生图模型）
    示例:
    ![](./example/example_gpt_image_edit.png)

6. **Gemini Image Generate** 节点生图（Google Gemini 3 Pro Image Preview 模型）
    示例：
    ![](./example/example_gemini_gen.png)

7. **Gemini Image Edit** 节点编辑图（Google Gemini 3 Pro Image Preview 模型）
    示例：
    ![](./example/example_gemini_image_edit.png)

## Troubleshooting
1. 如何创建正确的分组 API 令牌（api_key）? 
使用云雾API时，需要创建对应的 API 令牌（也就是 config.ini 的 api_key），API 令牌还有分组的概念，不同的组能调用模型的范围不同对应的价格也不同（倍率），具体可以通过这个链接查询：https://yunwu.ai/pricing 以 `gpt-image-1` 为例，目前仅支持 `纯AZ`、`官转`、`官转OpenAI`、`优质官转OpenAI`:
    ![](./example/gpt_image_token_group.png)

2. 遇到以下报错信息：“当前分组 纯AZ 下对于模型 gpt-image-1 无可用渠道”。
建议更换倍率更高的组，比如 `官转` 或者 `官转OpenAI`，保证稳定性（花费更多）

3. 如何查看费用使用情况？
使用云雾API时，可以通过【网页控制台】--【日志管理】--【使用日志】入口查看作业消耗的费用和时间等信息:
    ![](./example/yunwu_log.png)

## 特别鸣谢
1. [ComfyUI-MidjourneyNode-leoleexh](https://github.com/leoleelxh/ComfyUI-MidjourneyNode-leoleexh/tree/main) 提供了节点的布局和样式借鉴，感谢作者的贡献！

## 📩 Disclaimer | 免责申明

本工具仅供学习和研究使用，使用本工具所产生的任何后果由用户自行承担。 <br>

This tool is only for learning and research purposes, and any consequences arising from the use of this tool are borne
by the user.

## 💰 Buy Me a Coffee | 请我喝杯咖啡

<div align="center">
  <table>
    <tr>
      <td>
        <img src="./example/Alipay_20RMB.jpg" alt="buy_me_a_coffee" width="280"/><br>
      </td>
      <td>
        <img src="./example/Wechat_20RMB.jpg" alt="buy_me_a_coffee" width="280"/><br>
      </td>
    </tr>
  </table>
</div>
