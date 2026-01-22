import torch
import base64
import numpy as np
from PIL import Image
from io import BytesIO
import requests
import json

from .utils import load_config, init_logger


class GeminiImageEditNode:
    """ComfyUI 自定义节点：使用 Gemini 3 Pro Image Preview 模型编辑图片。

    输入：
        prompt (STRING): 文本提示词，描述要进行的编辑操作。
        image (IMAGE): 待编辑的图片。
    输出：
        IMAGE: 编辑后的图片（Tensor, 0~1, BxHxWxC）。
    """

    def __init__(self):
        self.logger = init_logger()
        config = load_config()
        # 优先读取 GEMINI_API
        if config.has_section('GEMINI_API'):
            api_section = config['GEMINI_API']
        else:
            api_section = {}

        self.api_key = api_section.get('api_key')
        self.api_url = api_section.get('api_url', 'https://yunwu.ai').rstrip('/')
        if not self.api_key:
            raise ValueError("API key not found in config.ini under [GEMINI_API] section")

    # ---------- ComfyUI 接口定义 ----------
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "image": ("IMAGE",),
            },
            "optional": {
                "aspect_ratio": (["1:1", "9:16", "16:9", "4:3", "3:4"], {"default": "1:1"}),
                "image_size": (["1K", "2K"], {"default": "1K"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "edit"
    CATEGORY = "MidjourneyHub"

    # ---------- 辅助函数 ----------
    @staticmethod
    def _tensor_to_base64(tensor: torch.Tensor) -> str:
        """将 ComfyUI 的图像 Tensor 转换为 base64 编码的字符串。"""
        if tensor.ndim == 4:
            tensor = tensor[0]
        
        img_np = (tensor.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        img_pil = Image.fromarray(img_np)
        
        buffer = BytesIO()
        img_pil.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        
        # 转换为 base64
        image_bytes = buffer.read()
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        
        return base64_data

    # ---------- 主功能 ----------
    def edit(self, prompt: str, image: torch.Tensor, aspect_ratio: str = "1:1", image_size: str = "1K"):
        """根据 prompt 和参考图片调用 API 生成编辑后的图片。"""
        try:
            # 将图片转换为 base64
            image_base64 = self._tensor_to_base64(image)
            
            # 构建请求 URL
            url = f"{self.api_url}/v1beta/models/gemini-3-pro-image-preview:generateContent?key={self.api_key}"
            
            # 构建请求体
            # 注意: test_api 示例显示使用 inline_data (snake_case) 而不是 inlineData (camelCase)
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"],
                    "imageConfig": {
                        "aspectRatio": aspect_ratio,
                        "imageSize": image_size
                    }
                }
            }

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            # 使用 requests 发送同步请求
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            self.logger.debug(f"Gemini API response: {data}")

            # 解析响应，提取图片数据
            tensors = []
            
            # 检查响应结构
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        # 尝试兼容 camelCase 和 snake_case
                        if 'inlineData' in part:
                            # 提取 base64 图片数据
                            inline_data = part['inlineData']
                            base64_data = inline_data.get('data', '')
                        elif 'inline_data' in part:
                            inline_data = part['inline_data']
                            base64_data = inline_data.get('data', '')
                        else:
                            continue
                            
                        if base64_data:
                            # 解码 base64 图片
                            image_bytes = base64.b64decode(base64_data)
                            img = Image.open(BytesIO(image_bytes)).convert("RGB")
                            img_np = np.array(img)
                            
                            # 转换为 ComfyUI 需要的 Tensor 格式
                            tensor = torch.from_numpy(img_np).float() / 255.0  # HWC
                            tensors.append(tensor)

            if not tensors:
                raise RuntimeError("No image data found in API response")

            # 将所有图片按 batch 维度堆叠
            img_tensor = torch.stack(tensors, dim=0)

            return (img_tensor,)

        except Exception as e:
            self.logger.error(f"Error in GeminiImageEditNode: {str(e)}")
            raise
