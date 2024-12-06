import torch
from .api_client import MJClient


class MidjourneyActionNode:
    def __init__(self):
        self.api_client = MJClient()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "task_id": ("STRING", {"multiline": False}),
                "action": (["U1", "U2", "U3", "U4", "V1", "V2", "V3", "V4"], {"default": "U1"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale_or_vary"
    CATEGORY = "image"

    def upscale_or_vary(self, task_id, action):
        # Start the upscale or variation process
        subtask_id = self.api_client.upscale_or_vary(task_id, action)

        # Wait for the process to complete and get the resulting image
        result_image, _, _ = self.api_client.sync_mj_status(subtask_id)

        # Convert the image to a tensor that ComfyUI can use
        img_tensor = torch.from_numpy(result_image).float() / 255.0
        img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension

        return (img_tensor,)
