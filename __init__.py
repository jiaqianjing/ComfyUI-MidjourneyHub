from .midjourney_imagine_node import MidjourneyImagineNode
from .midjourney_action_node import MidjourneyActionNode, MidjourneyBatchActionNode
from .midjourney_blend_node import MidjourneyBlendNode
from .gpt_image_generate_node import GPTImageGenerateNode

NODE_CLASS_MAPPINGS = {
    "MidjourneyImagineNode": MidjourneyImagineNode,
    "MidjourneyActionNode": MidjourneyActionNode,
    "MidjourneyBatchActionNode": MidjourneyBatchActionNode,
    "MidjourneyBlendNode": MidjourneyBlendNode,
    "GPTImageGenerateNode": GPTImageGenerateNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MidjourneyImagineNode": "MidjourneyImagineNode",
    "MidjourneyActionNode": "Midjourney Upscale/Variation",
    "MidjourneyBatchActionNode": "Midjourney Batch Upscale/Variation",
    "MidjourneyBlendNode": "Midjourney Blend (Image Mix)",
    "GPTImageGenerateNode": "GPT Image Generate"
}
