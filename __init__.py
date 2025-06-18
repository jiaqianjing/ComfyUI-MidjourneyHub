from .midjourney_imagine_node import MidjourneyImagineNode
from .midjourney_action_node import MidjourneyActionNode, MidjourneyBatchActionNode
from .midjourney_blend_node import MidjourneyBlendNode

NODE_CLASS_MAPPINGS = {
    "MidjourneyImagineNode": MidjourneyImagineNode,
    "MidjourneyActionNode": MidjourneyActionNode,
    "MidjourneyBatchActionNode": MidjourneyBatchActionNode,
    "MidjourneyBlendNode": MidjourneyBlendNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MidjourneyImagineNode": "MidjourneyImagineNode",
    "MidjourneyActionNode": "Midjourney Upscale/Variation",
    "MidjourneyBatchActionNode": "Midjourney Batch Upscale/Variation",
    "MidjourneyBlendNode": "Midjourney Blend (Image Mix)"
}
