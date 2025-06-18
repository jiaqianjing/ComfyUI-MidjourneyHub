import torch
import base64
import numpy as np
from PIL import Image
from io import BytesIO

from openai import OpenAI

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

        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        return self._client

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
                "model": (["gpt-image-1", "dall-e-2"], {"default": "gpt-image-1"}),
                "background": (["auto", "transparent", "opaque"], {"default": "auto"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "output_compression": ("INT", {"default": 100, "min": 0, "max": 100, "step": 1}),
                "quality": (["auto", "high", "medium", "low"], {"default": "auto"}),
                "size": (["auto", "1024x1024", "1536x1024", "1024x1536"], {"default": "auto"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "edit"
    CATEGORY = "image"

    # ---------- 辅助函数 ----------
    @staticmethod
    def _tensor_to_bytesio(tensor: torch.Tensor) -> BytesIO:
        """将 ComfyUI 的图像 Tensor 转换为 PNG 格式的 BytesIO 对象。"""
        if tensor.ndim == 4:
            tensor = tensor[0]
        
        img_np = (tensor.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        img_pil = Image.fromarray(img_np)
        
        buffer = BytesIO()
        img_pil.save(buffer, format="PNG")
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
             model: str = "gpt-image-1", background: str = "auto", n: int = 1,
             output_format: str = "png", output_compression: int = 100,
             quality: str = "auto", size: str = "auto"):
        """根据 prompt 和参考图片调用 API 生成新图片。"""
        try:
            # 收集所有有效的图像输入
            images = [img for img in [image1, image2, image3, image4] if img is not None]
            if not images:
                raise ValueError("At least one image must be provided.")

            # 将 Tensor 转换为 BytesIO 对象列表
            image_files = [self._tensor_to_bytesio(img) for img in images]

            # 构建 API 调用参数
            kwargs = {
                "prompt": prompt,
                "model": model,
                "image": image_files,
                "n": n,
            }

            if mask is not None:
                kwargs["mask"] = self._mask_tensor_to_bytesio(mask)
            
            # 仅 gpt-image-1 支持的参数
            if model == "gpt-image-1":
                kwargs.update({
                    "background": background,
                    "output_format": output_format,
                    "output_compression": output_compression,
                    "quality": quality,
                    "size": size,
                })

            # 调用 API
            response = self.client.images.edit(**kwargs)

            if not response or not response.data:
                raise RuntimeError("Empty response from the image editing API")

            # 处理返回的 base64 数据
            tensors = []
            for item in response.data:
                b64_data = item.b64_json
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