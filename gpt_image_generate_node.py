import torch
import base64
import numpy as np
from PIL import Image
from io import BytesIO

from openai import OpenAI

from .utils import load_config, init_logger


class GPTImageGenerateNode:
    """ComfyUI 自定义节点：使用 GPT-Image-1 模型生成图片。

    输入：
        prompt (STRING): 文本提示词，支持多行。
    输出：
        IMAGE: 生成的图片（Tensor, 0~1, BxHxWxC）。
    """

    def __init__(self):
        self.logger = init_logger()
        config = load_config()
        # 优先读取 GPT_IMAGE_API
        if config.has_section('GPT_IMAGE_API'):
            api_section = config['GPT_IMAGE_API']
        else:
            api_section = {}

        self.api_key = api_section.get('api_key')
        base_url_root = api_section.get('api_url', 'https://yunwu.ai').rstrip('/')
        # GPT-Image-1 端点位于 /v1
        self.base_url = f"{base_url_root}/v1"
        if not self.api_key:
            raise ValueError("API key not found in config.ini under [GPT_IMAGE_API] section")

        # 延迟初始化，避免在导入阶段占用资源
        self._client = None

    @property
    def client(self):
        if self._client is None:
            # 在首次调用时创建 OpenAI 客户端
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        return self._client

    # ---------- ComfyUI 接口定义 ----------
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "model": (["gpt-image-1"], {"default": "gpt-image-1"}),
                "background": (["auto", "transparent", "opaque"], {"default": "auto"}),
                "moderation": (["auto", "low"], {"default": "auto"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "output_compression": ("INT", {"default": 100, "min": 0, "max": 100, "step": 1}),
                "quality": (["auto", "high", "medium", "low"], {"default": "auto"}),
                "size": (["auto", "1024x1024", "1536x1024", "1024x1536"], {"default": "auto"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "image"

    # ---------- 主功能 ----------
    def generate(self, prompt: str, model="gpt-image-1", background="auto", moderation="auto", n: int = 1,
                output_format="png", output_compression: int = 100, quality="auto", size="auto"):
        """根据 prompt 调用 GPT-Image-1 生成图片。"""
        try:
            # 组装调用参数（只传递用户显式设置或与默认不同的参数）
            kwargs = {
                "prompt": prompt,
                "model": model,
                "n": n,
            }

            # 仅 gpt-image-1 支持的参数，其他模型传递会被忽略或导致错误——因此按需添加
            if model == "gpt-image-1":
                kwargs.update({
                    "background": background,
                    "moderation": moderation,
                    "output_format": output_format,
                    "output_compression": output_compression,
                    "quality": quality,
                    "size": size,
                })

            response = self.client.images.generate(**kwargs)
            if not response or not response.data:
                raise RuntimeError("Empty response from GPT-Image-1 API")

            tensors = []
            for item in response.data:
                b64_data = item.b64_json
                if not b64_data:
                    raise RuntimeError("Missing base64 image in response item")

                image_bytes = base64.b64decode(b64_data)
                img = Image.open(BytesIO(image_bytes)).convert("RGB")
                img_np = np.array(img)

                tensor = torch.from_numpy(img_np).float() / 255.0  # HWC
                tensors.append(tensor)

            # 将所有图片按 batch 维度堆叠
            img_tensor = torch.stack(tensors, dim=0)

            return (img_tensor,)
        except Exception as e:
            self.logger.error(f"Error in GPTImageGenerateNode: {str(e)}")
            raise 