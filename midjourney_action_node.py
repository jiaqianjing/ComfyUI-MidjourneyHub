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


class MidjourneyBatchActionNode:
    def __init__(self):
        self.api_client = MJClient()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "task_id": ("STRING", {"multiline": False}),
                "batch_actions": (["U1-U4", "V1-V4"], {"default": "U1-U4"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("image1", "image2", "image3", "image4")
    FUNCTION = "batch_process"
    CATEGORY = "MidjourneyHub"

    def batch_process(self, task_id, batch_actions):
        # Determine which actions to perform
        if batch_actions == "U1-U4":
            actions = ["U1", "U2", "U3", "U4"]
        else:  # V1-V4
            actions = ["V1", "V2", "V3", "V4"]
            
        # Process all actions in parallel
        results = self.api_client.batch_upscale_or_vary(task_id, actions)
        
        # Prepare return values - pad with None if we have less than 4 results
        padded_results = results + [None] * (4 - len(results))
        
        # Flatten the results for return
        flat_results = []
        for img in padded_results:
            # Convert numpy array to torch tensor if image exists
            if img is not None:
                img_tensor = torch.from_numpy(img).float() / 255.0
                img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension
            else:
                img_tensor = None
            flat_results.append(img_tensor)
            
        return tuple(flat_results)
