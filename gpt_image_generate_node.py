import torch
import base64
import numpy as np
from PIL import Image
from io import BytesIO
import requests
import json

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

    # ---------- ComfyUI 接口定义 ----------
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "model": (["gpt-image-2-all", "gpt-image-1.5", "gpt-image-1"], {"default": "gpt-image-2-all"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "quality": (["auto", "high", "medium", "low"], {"default": "auto"}),
                "size": (["auto", "1024x1024", "1536x1024", "1024x1536"], {"default": "auto"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "MidjourneyHub"

    # ---------- 主功能 ----------
    def generate(self, prompt: str, model="gpt-image-1.5", n: int = 1, quality="auto", size="auto"):
        """根据 prompt 调用 GPT-Image-1 生成图片。"""
        try:
            url = f"{self.base_url}/images/generations"
            
            # 组装调用参数 (仅使用 API 支持的参数)
            payload_data = {
                "prompt": prompt,
                "model": model,
                "n": n,
                "quality": quality,
                "size": size,
                "response_format": "b64_json"  # 必须指定以获取图片数据
            }

            payload = json.dumps(payload_data)
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, data=payload, timeout=120)  # 120秒超时
            response.raise_for_status() # 检查 HTTP 错误
            
            data = response.json()
            if not data or 'data' not in data:
                raise RuntimeError(f"Invalid response from GPT-Image-1 API: {response.text}")

            tensors = []
            for item in data['data']:
                b64_data = item.get('b64_json')
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
 