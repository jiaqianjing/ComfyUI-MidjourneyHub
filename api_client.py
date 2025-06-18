import os
import json
import numpy as np
from PIL import Image
from io import BytesIO
from .utils import init_logger, load_config
import asyncio
import aiohttp
import base64

logger = init_logger()
config = load_config()

logger.info(f"config: {config}")

class MJClient:
    def __init__(self):
        self.api_url = config['MIDJOURNEY_API']['api_url']
        self.api_key = config['MIDJOURNEY_API']['api_key']


    async def imagine(self, text_prompt) -> str:
        """
        return task_id
        """
        logger.debug(f"Imagine with prompt: {text_prompt}")
        url = f"{self.api_url}/mj/submit/imagine" 
        payload = json.dumps({
            "base64Array": [],
            "notifyHook": "",
            "prompt": text_prompt,
            "state": "",
            "botType": "MID_JOURNEY"
        })
        headers = {
            'Authorization': 'Bearer {}'.format(self.api_key),
            'Content-Type': 'application/json; charset=utf-8'
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=payload) as response:
                    response.raise_for_status()
                    # 首先尝试读取原始文本
                    text = await response.text()
                    try:
                        # 尝试将文本解析为 JSON
                        result = json.loads(text)
                    except json.JSONDecodeError:
                        # 如果不是 JSON 格式，直接使用文本作为结果
                        logger.debug(f"Response is plain text: {text}")
                        result = {"result": text.strip()}
                    
                    logger.debug(f"Imagine response: {result}")
                    return result.get("result", None)
        except Exception as e:
            logger.error(f"Error during Imagine: {e}")
            raise

    async def _submit_upscale_vary_task(self, task_id, custom_id, session):
        """封装提交放大/变体任务的通用逻辑"""
        url = f"{self.api_url}/mj/submit/action"
        payload = json.dumps({
            "chooseSameChannel": True,
            "customId": custom_id,
            "taskId": task_id,
            "notifyHook": "",
            "state": ""
        })
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        async with session.post(url, headers=headers, data=payload) as response:
            response.raise_for_status()
            text = await response.text()
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                logger.debug(f"Response is plain text: {text}")
                result = {"result": text.strip()}
            
            return result.get("result", None)

    async def upscale_or_vary(self, task_id="", action="U1"):
        """
        执行单个放大或变体操作
        return: image
        """
        try:
            _, _, buttons = await self.sync_mj_status(task_id)
            custom_id = buttons[action]
            
            async with aiohttp.ClientSession() as session:
                subtask_id = await self._submit_upscale_vary_task(task_id, custom_id, session)
                if not subtask_id:
                    raise ValueError("Failed to get subtask_id")
                
                image, _, _ = await self.sync_mj_status(task_id=subtask_id)
                return image
                
        except Exception as e:
            logger.error(f"Error during Upscale/Vary: {e}")
            raise

    async def sync_mj_status(self, task_id):
        """
        异步轮询任务状态
        return image, task_id, buttons 
        """
        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f"{self.api_url}/mj/task/{task_id}/fetch"
                    headers = {
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json; charset=utf-8'
                    }
                    
                    async with session.get(url, headers=headers) as response:
                        response.raise_for_status()
                        # 首先读取原始文本
                        text = await response.text()
                        try:
                            # 尝试将文本解析为 JSON
                            data = json.loads(text)
                        except json.JSONDecodeError:
                            logger.debug(f"Response is plain text: {text}")
                            raise ValueError(f"Expected JSON response but got: {text}")
                        
                        logger.debug(f"Fetch response: {data}")
                        
                        status = data['status']
                        if status == 'SUCCESS':
                            img = None
                            if 'imageUrl' in data:
                                img = await self.download_image(data['imageUrl'])
                            if 'buttons' in data:
                                buttons = {
                                    button['label']: button['customId'] 
                                    for button in data['buttons']
                                }
                            return img, task_id, buttons
                        
                        elif status in ['FAILED', 'FAILURE']:
                            # 统一处理失败与超时 (FAILURE) 状态，将具体 failReason 抛出供上层 (ComfyUI) 捕获
                            raise Exception(f"Task failed: {data.get('failReason', 'Unknown error')}")
                        
                        elif status in ['', 'SUBMITTED', 'IN_PROGRESS', 'NOT_START']:
                            logger.info(f"Task status: {status}, progress: {data.get('progress', 'Unknown')}")
                            await asyncio.sleep(3)  # 异步等待3秒
                        
                        else:
                            raise Exception(f"Unknown task status: {data['status']}")
                        
        except Exception as e:
            logger.error(f"Error during sync_mj_status: {e}")
            raise

    async def download_image(self, url):
        """异步下载图片并转换为numpy数组"""
        logger.debug(f"Downloading image from URL: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    image_data = await response.read()
                    img = Image.open(BytesIO(image_data))
                    return np.array(img)
        except Exception as e:
            logger.error(f"Error downloading image from URL {url}: {str(e)}")
            raise

    def image_to_base64(self, image_path):
        """
        将图片文件转换为 base64 格式

        Args:
            image_path (str): 图片文件路径

        Returns:
            str: base64 编码的图片数据，格式如 "data:image/png;base64,xxx"
        """
        try:
            with open(image_path, "rb") as image_file:
                # 读取图片数据
                image_data = image_file.read()
                # 转换为 base64
                base64_data = base64.b64encode(image_data).decode('utf-8')

                # 根据文件扩展名确定 MIME 类型
                file_extension = os.path.splitext(image_path)[1].lower()
                if file_extension in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif file_extension == '.png':
                    mime_type = 'image/png'
                elif file_extension == '.gif':
                    mime_type = 'image/gif'
                elif file_extension == '.webp':
                    mime_type = 'image/webp'
                else:
                    # 默认使用 png
                    mime_type = 'image/png'

                return f"data:{mime_type};base64,{base64_data}"
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            raise

    async def blend(self, base64_images, dimensions="SQUARE", bot_type="MID_JOURNEY", quality=None, notify_hook="", state=""):
        """
        提交 Blend 任务（图片混合）

        Args:
            base64_images (list): 图片base64数组，格式如 ["data:image/png;base64,xxx1", "data:image/png;base64,xxx2"]
            dimensions (str): 图片比例，可选值: "PORTRAIT"(2:3), "SQUARE"(1:1), "LANDSCAPE"(3:2)
            bot_type (str): bot类型，可选值: "MID_JOURNEY", "NIJI_JOURNEY"
            quality (str): 图像质量，可选值: "hd"
            notify_hook (str): 回调地址，为空时使用全局notifyHook
            state (str): 自定义参数

        Returns:
            str: task_id
        """
        logger.debug(f"Blend with {len(base64_images)} images, dimensions: {dimensions}")
        url = f"{self.api_url}/mj/submit/blend"

        payload_data = {
            "botType": bot_type,
            "base64Array": base64_images,
            "dimensions": dimensions,
            "notifyHook": notify_hook,
            "state": state
        }

        # 只有当 quality 不为 None 时才添加到 payload 中
        if quality is not None:
            payload_data["quality"] = quality

        payload = json.dumps(payload_data)

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json; charset=utf-8'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=payload) as response:
                    response.raise_for_status()
                    # 首先尝试读取原始文本
                    text = await response.text()
                    try:
                        # 尝试将文本解析为 JSON
                        result = json.loads(text)
                    except json.JSONDecodeError:
                        # 如果不是 JSON 格式，直接使用文本作为结果
                        logger.debug(f"Response is plain text: {text}")
                        result = {"result": text.strip()}

                    logger.debug(f"Blend response: {result}")
                    return result.get("result", None)
        except Exception as e:
            logger.error(f"Error during Blend: {e}")
            raise


    async def batch_upscale_or_vary(self, task_id, actions=["U1", "U2", "U3", "U4"]):
        """
        批量处理多个放大或变体任务
        return: List[Image]
        """
        try:
            _, _, buttons = await self.sync_mj_status(task_id)

            async def submit_task(action):
                try:
                    custom_id = buttons[action]
                    subtask_id = await self._submit_upscale_vary_task(task_id, custom_id, session)
                    if subtask_id:
                        logger.debug(f"Submitted {action} task: {subtask_id}")
                        return action, subtask_id
                except Exception as e:
                    logger.error(f"Error submitting {action} task: {e}")
                    return None

            async with aiohttp.ClientSession() as session:
                tasks = [submit_task(action) for action in actions]
                results = await asyncio.gather(*tasks)
                subtask_ids = [r for r in results if r is not None]

            tasks = [self.sync_mj_status(subtask_id) for _, subtask_id in subtask_ids]
            results = []
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

            for (action, subtask_id), task_result in zip(subtask_ids, completed_tasks):
                if isinstance(task_result, Exception):
                    logger.error(f"Error processing {action} task {subtask_id}: {task_result}")
                    continue
                image, _, _ = task_result
                results.append(image)
                logger.debug(f"Completed {action} task: {subtask_id}")

            return results
        except Exception as e:
            logger.error(f"Error during batch upscale/vary: {e}")
            raise
