from .midjourney_imagine_node import MidjourneyImagineNode
from .midjourney_action_node import MidjourneyActionNode, MidjourneyBatchActionNode

NODE_CLASS_MAPPINGS = {
    "MidjourneyImagineNode": MidjourneyImagineNode,
    "MidjourneyActionNode": MidjourneyActionNode,
    "MidjourneyBatchActionNode": MidjourneyBatchActionNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MidjourneyImagineNode": "MidjourneyImagineNode",
    "MidjourneyActionNode": "Midjourney Upscale/Variation",
    "MidjourneyBatchActionNode": "Midjourney Batch Upscale/Variation"
}
