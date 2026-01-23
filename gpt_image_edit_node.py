import torch
import base64
import numpy as np
from PIL import Image
from io import BytesIO
import requests
import json

from .utils import load_config, init_logger


class GPTImageEditNode:
    """ComfyUI 自定义节点：使用 GPT-Image-1 模型编辑/合成图片。

    输入：
        prompt (STRING): 文本提示词。
        image1 (IMAGE):  必需的参考图片。
        image2-4 (IMAGE): 可选的额外参考图片。

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
        self.base_url = f"{base_url_root}/v1"
        if not self.api_key:
            raise ValueError("API key not found in config.ini under [GPT_IMAGE_API] section")

    # ---------- ComfyUI 接口定义 ----------
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "image1": ("IMAGE",),
            },
            "optional": {
                "image2": ("IMAGE",),
                "image3": ("IMAGE",),
                "image4": ("IMAGE",),
                "mask": ("MASK",),
                "model": (["gpt-image-1.5", "gpt-image-1", "dall-e-2"], {"default": "gpt-image-1.5"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "quality": (["auto", "high", "medium", "low"], {"default": "auto"}),
                "size": (["auto", "1024x1024", "1536x1024", "1024x1536"], {"default": "auto"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "edit"
    CATEGORY = "MidjourneyHub"

    # ---------- 辅助函数 ----------
    @staticmethod
    def _tensor_to_bytesio(tensor: torch.Tensor, format="PNG") -> BytesIO:
        """将 ComfyUI 的图像 Tensor 转换为指定格式的 BytesIO 对象。"""
        if tensor.ndim == 4:
            tensor = tensor[0]
        
        img_np = (tensor.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        img_pil = Image.fromarray(img_np)
        
        buffer = BytesIO()
        img_pil.save(buffer, format=format)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _mask_tensor_to_bytesio(tensor: torch.Tensor) -> BytesIO:
        """
        将 ComfyUI MASK tensor 转换为带 alpha 通道的 PNG BytesIO。
        API 要求编辑区域为透明 (alpha=0)。ComfyUI 蒙版中值为 1.0 的区域是要编辑的区域。
        因此，我们将蒙版中值为 1.0 的区域映射为 alpha 0。
        """
        if tensor.ndim == 3:  # (B, H, W)
            tensor = tensor.squeeze(0)  # (H, W)

        # 反转蒙版: 1.0 (编辑) -> 0.0 (透明), 0.0 (不编辑) -> 1.0 (不透明)
        # API 通过 alpha=0 的区域来识别要编辑的位置
        alpha_channel = (1.0 - tensor.cpu().numpy()) * 255.0
        alpha_channel = np.clip(alpha_channel, 0, 255).astype(np.uint8)

        # 创建一个带有此 alpha 通道的 RGBA 图像
        pil_image = Image.fromarray(alpha_channel, mode='L').convert('RGBA')
        
        # 将原始的 alpha 通道数据放入
        pil_image.putalpha(Image.fromarray(alpha_channel, mode='L'))

        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # ---------- 主功能 ----------
    def edit(self, prompt: str, image1: torch.Tensor, image2: torch.Tensor = None, 
             image3: torch.Tensor = None, image4: torch.Tensor = None, mask: torch.Tensor = None,
             model: str = "gpt-image-1.5", n: int = 1,
             quality: str = "auto", size: str = "auto"):
        """根据 prompt 和参考图片调用 API 生成新图片。"""
        try:
            url = f"{self.base_url}/images/edits"

            # 收集所有有效的图像输入
            images = [img for img in [image1, image2, image3, image4] if img is not None]
            if not images:
                raise ValueError("At least one image must be provided.")

            # 构建 multipart/form-data 的 files 参数
            # 注意：test_api 示例中使用了多个 'image' 键，requests 的 files 参数支持 list of tuples
            # 格式: ('field_name', ('filename', file_object, 'content_type'))
            files = []
            for idx, img in enumerate(images):
                # 默认使用 PNG，如果 API 有特殊要求可以调整
                file_obj = self._tensor_to_bytesio(img, format="PNG")
                files.append(('image', (f'image{idx}.png', file_obj, 'image/png')))

            if mask is not None:
                mask_obj = self._mask_tensor_to_bytesio(mask)
                files.append(('mask', ('mask.png', mask_obj, 'image/png')))

            # 构建其他参数 payload (仅使用 API 支持的参数)
            # requests 的 files 和 data 配合使用时，data 中的字段会作为 form fields 发送
            payload = {
                "prompt": prompt,
                "model": model,
                "n": n,
                "quality": quality,
                "size": size,
                "response_format": "b64_json"  # 强制返回 base64
            }

            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
                # 'Content-Type': 'multipart/form-data' # requests 会自动添加 boundary，不要手动添加 Content-Type
            }

            # 发送请求 (120秒超时，图像生成较慢)
            response = requests.post(url, headers=headers, data=payload, files=files, timeout=120)
            response.raise_for_status()

            data = response.json()
            if not data or 'data' not in data:
                 raise RuntimeError(f"Invalid response from GPT-Image-1 API: {response.text}")

            # 处理返回的 base64 数据
            tensors = []
            for item in data['data']:
                b64_data = item.get('b64_json')
                if not b64_data:
                    raise RuntimeError("No base64 image data in response")

                image_bytes = base64.b64decode(b64_data)
                img = Image.open(BytesIO(image_bytes)).convert("RGB")
                img_np = np.array(img)

                # 转换为 ComfyUI 需要的 Tensor 格式
                tensor = torch.from_numpy(img_np).float() / 255.0
                tensors.append(tensor)

            if not tensors:
                 raise RuntimeError("No images were generated from the API")

            img_tensor = torch.stack(tensors, dim=0)  # 添加 batch 维

            return (img_tensor,)
        except Exception as e:
            self.logger.error(f"Error in GPTImageEditNode: {str(e)}")
            raise
 