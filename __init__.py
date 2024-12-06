from .midjourney_imagine_node import MidjourneyImagineNode
from .midjourney_action_node import MidjourneyActionNode

NODE_CLASS_MAPPINGS = {
    "MidjourneyImagineNode": MidjourneyImagineNode,
    "MidjourneyActionNode": MidjourneyActionNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MidjourneyImagineNode": "MidjourneyImagineNode",
    "MidjourneyActionNode": "Midjourney Upscale/Variation"
}
