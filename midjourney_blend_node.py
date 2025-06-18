import torch
import asyncio
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import time

from .api_client import MJClient


class MidjourneyBlendNode:
    """ComfyUI 自定义节点：将两张图片上传至 Midjourney Blend 接口进行融合。

    输入：
        image1, image2: IMAGE 类型（Tensor），数值范围 0~1，shape 支持 (B,H,W,C) / (H,W,C) / (C,H,W)。

    可选：
        dimensions: 图片比例，PORTRAIT / SQUARE / LANDSCAPE
        bot_type:    机器人类型，MID_JOURNEY / NIJI_JOURNEY
        quality:     画质，可传 "hd" 或留空
        seed:        随机种子，用于避免缓存

    输出：
        融合后的图片、任务 ID、操作按钮字典。
    """

    def __init__(self):
        self.api_client = MJClient()

    # ---------- ComfyUI 接口定义 ----------
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
            },
            "optional": {
                "dimensions": (["PORTRAIT", "SQUARE", "LANDSCAPE"], {"default": "SQUARE"}),
                "bot_type": (["MID_JOURNEY", "NIJI_JOURNEY"], {"default": "MID_JOURNEY"}),
                "quality": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2**31-1, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "DICT")
    RETURN_NAMES = ("image", "task_id", "buttons")
    FUNCTION = "blend_images"
    CATEGORY = "image"

    # ---------- 辅助函数 ----------
    @staticmethod
    def _tensor_to_base64(img_tensor):
        """将 ComfyUI 的图像 Tensor 转换为 base64 字符串 (data:image/png;base64,XXX)"""
        # 移除 batch 维
        if img_tensor.ndim == 4:
            img_tensor = img_tensor[0]

        # 处理 CHW -> HWC
        if img_tensor.shape[0] in (1, 3) and img_tensor.shape[0] < 10:  # 简单判断 C 在前
            img_tensor = img_tensor.permute(1, 2, 0)

        # 转换为 numpy，并将 0~1 float 转换成 0~255 uint8
        img_np = (img_tensor.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        img_pil = Image.fromarray(img_np)

        buffer = BytesIO()
        img_pil.save(buffer, format="PNG")
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{base64_str}"

    # ---------- 主功能 ----------
    def blend_images(self, image1, image2, dimensions="SQUARE", bot_type="MID_JOURNEY", quality="", seed=-1):
        try:
            # 计算唯一 state，以避免后端将相同参数视为重复任务
            if seed == -1:
                state_val = str(int(time.time() * 1000))  # 毫秒时间戳
            else:
                state_val = str(seed)

            # 准备 base64 输入
            base64_images = [
                self._tensor_to_base64(image1),
                self._tensor_to_base64(image2),
            ]

            # 获取或创建事件循环（在 ComfyUI 环境中经常已存在）
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 异步调用 blend 接口
            task_id = loop.run_until_complete(
                self.api_client.blend(
                    base64_images=base64_images,
                    dimensions=dimensions,
                    bot_type=bot_type,
                    quality=quality if quality else None,
                    state=state_val,
                )
            )
            if not task_id:
                raise ValueError("Failed to get task_id from Midjourney API (blend)")

            # 轮询等待结果
            image, task_id_fetched, buttons = loop.run_until_complete(
                self.api_client.sync_mj_status(task_id=task_id)
            )

            # 转换为 ComfyUI 需要的 Tensor 格式
            img_tensor = torch.from_numpy(image).float() / 255.0  # HWC -> 0~1
            img_tensor = img_tensor.unsqueeze(0)  # 添加 batch 维

            return (img_tensor, task_id_fetched, buttons)

        except Exception as e:
            print(f"Error in MidjourneyBlendNode: {str(e)}")
            raise 