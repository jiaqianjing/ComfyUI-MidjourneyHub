# 简介
该节点可以在 ComfyUI 中使用各种主流商业模型绘图节点，目前后端是使用**云雾 API** 提供的 API 支持。可以通过这个链接进行注册和使用：[https://yunwu.ai/register?aff=ubgH](https://yunwu.ai/register?aff=ubgH)

## 更新
* 2025.06.18 新增 midjourney **[Blend(Image Mix)]** 节点，可上传两张图进行融合，支持 `seed` 避免缓存;
* 2024.12.13 引入协程的方式改造原始同步方法，通过并发加快创建图片和同步状态的响应尤其是 [Batch Upsale/Variation] 节点;
* 2024.12.10 支持 midjourney **[Batch Upsale/Variation]** 节点;
* 2024.12.06 支持 midjourney **[Imagine] 和 [Upsale/Variation]** 节点;

## 当前价格

> 本项目不会产生任何费用，以下费用出自调用云雾 Midjourney API，总结：4格主图（mj_imagine）是 0.15元/张，基于主图放大后的子图(mj_upscale) 0.075元/张; 如果用批节点输出一张主图+四张放大子图，那么总费用是 0.15+0.075*4=0.45元/张，每张是 0.45/4=0.1125元/张（因为主图没啥用，所以不计入费用）

* 云雾价格主页: [https://yunwu.ai/pricing](https://yunwu.ai/pricing)
![](./example/pricing.png)

## 使用方法
### 1. 修改自己的 api_url/api_key
![](./example/config.png)
* [注]：因为后端 API 使用的云雾 API，他们可能不定期修改域名（api_url）

### 2. 工作流
1. [Imagine] 节点 + [Upsale/Variation] 节点
![](./example/example.png)

2. [Imagine] 节点 + [Batch Upsale/Variation] 节点
![](./example/example_batch_upscale.png)

3. **Blend(Image Mix)** 节点（两张图片融合）
    
    示例1:
    ![](./example/example_mj_blend_01.png)

    示例2:
    ![](./example/example_mj_blend_02.png)

## 特别鸣谢
1. [ComfyUI-MidjourneyNode-leoleexh](https://github.com/leoleelxh/ComfyUI-MidjourneyNode-leoleexh/tree/main) 提供了节点的布局和样式借鉴，感谢作者的贡献！
