from .midjourney_imagine_node import MidjourneyImagineNode
from .midjourney_action_node import MidjourneyActionNode, MidjourneyBatchActionNode
from .midjourney_blend_node import MidjourneyBlendNode
from .gpt_image_generate_node import GPTImageGenerateNode
from .gpt_image_edit_node import GPTImageEditNode
from .gemini_image_generate_node import GeminiImageGenerateNode
from .gemini_image_edit_node import GeminiImageEditNode

NODE_CLASS_MAPPINGS = {
    "MidjourneyImagineNode": MidjourneyImagineNode,
    "MidjourneyActionNode": MidjourneyActionNode,
    "MidjourneyBatchActionNode": MidjourneyBatchActionNode,
    "MidjourneyBlendNode": MidjourneyBlendNode,
    "GPTImageGenerateNode": GPTImageGenerateNode,
    "GPTImageEditNode": GPTImageEditNode,
    "GeminiImageGenerateNode": GeminiImageGenerateNode,
    "GeminiImageEditNode": GeminiImageEditNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MidjourneyImagineNode": "MidjourneyImagineNode",
    "MidjourneyActionNode": "Midjourney Upscale/Variation",
    "MidjourneyBatchActionNode": "Midjourney Batch Upscale/Variation",
    "MidjourneyBlendNode": "Midjourney Blend (Image Mix)",
    "GPTImageGenerateNode": "GPT Image Generate",
    "GPTImageEditNode": "GPT Image Edit",
    "GeminiImageGenerateNode": "Gemini Image Generate",
    "GeminiImageEditNode": "Gemini Image Edit"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
