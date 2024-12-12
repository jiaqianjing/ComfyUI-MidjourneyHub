import torch
import asyncio
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
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 直接获取结果图片
            result_image = loop.run_until_complete(
                self.api_client.upscale_or_vary(task_id, action)
            )

            # 转换图像格式
            img_tensor = torch.from_numpy(result_image).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0)

            return (img_tensor,)
        except Exception as e:
            print(f"Error in MidjourneyActionNode: {str(e)}")
            raise
        


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
        try:
            # 获取或创建事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop()

            # 确定要执行的操作
            if batch_actions == "U1-U4":
                actions = ["U1", "U2", "U3", "U4"]
            else:  # V1-V4
                actions = ["V1", "V2", "V3", "V4"]

            # 异步调用
            results = loop.run_until_complete(
                self.api_client.batch_upscale_or_vary(task_id, actions)
            )
            
            # 处理结果(如果返回的数量不足 actions 的长度，用 None 补足)
            padded_results = results + [None] * (len(actions) - len(results))
            flat_results = []

            for img in padded_results:
                if img is not None:
                    img_tensor = torch.from_numpy(img).float() /255.0
                    img_tensor = img_tensor.unsqueeze(0)
                else:
                    img_tensor = None
                flat_results.append(img_tensor)
            return tuple(flat_results)
        except Exception as e:
            print(f"Error in MidjourneyBatchActionNode: {str(e)}")
            raise

