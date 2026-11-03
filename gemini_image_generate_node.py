"""ComfyUI Gemini node: prompt/options -> IMAGE batch; calls Yunwu HTTP API."""
import requests

from .utils import load_config, init_logger
from .image_model_options import GEMINI_MODELS, validate_gemini_options
from .image_response import decode_gemini_images

class GeminiImageGenerateNode:
    """ComfyUI 自定义节点：使用 Gemini 3 Pro Image Preview 模型生成图片。

    输入：
        prompt (STRING): 文本提示词，支持多行。
    输出：
        IMAGE: 生成的图片（Tensor, 0~1, BxHxWxC）。
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
            },
            "optional": {
                "aspect_ratio": (["1:1", "9:16", "16:9", "4:3", "3:4"], {"default": "1:1"}),
                "image_size": (["1K", "2K"], {"default": "1K"}),
                "model": (GEMINI_MODELS, {"default": GEMINI_MODELS[0]}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "MidjourneyHub"

    # ---------- 主功能 ----------
    def generate(self, prompt: str, aspect_ratio: str = "1:1", image_size: str = "1K", model: str = "gemini-3-pro-image-preview"):
        """根据 prompt 调用 Gemini 3 Pro Image Preview 生成图片。"""
        validate_gemini_options(model, aspect_ratio, image_size)
        try:
            # 构建请求 URL
            url = f"{self.api_url}/v1beta/models/{model}:generateContent"
            
            # 构建请求体
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
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

            # BLOCKING REQUEST
            response = requests.post(url, headers=headers, json=payload, timeout=180)
            response.raise_for_status()
            return (decode_gemini_images(response.json()),)

        except Exception as e:
            self.logger.error(f"Error in GeminiImageGenerateNode: {str(e)}")
            raise
