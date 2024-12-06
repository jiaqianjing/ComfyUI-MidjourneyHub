import os
import json
import time
import requests
import numpy as np
from PIL import Image
from io import BytesIO
from .utils import init_logger, load_config

logger = init_logger()
config = load_config()

logger.info(f"config: {config}")

class MJClient:
    def __init__(self):
        self.api_url = config['MIDJOURNEY_API']['api_url']
        self.api_key = config['MIDJOURNEY_API']['api_key']


    def imagine(self, text_prompt) -> str:
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
            """ response body example:
            { 
                "code":1,
                "description":"In queue, there are 9 tasks ahead",
                "result":"1732502563006031",
                "properties":
                    {
                        "numberOfQueues":9,
                        "discordChannelId":"1300478254200782858",
                        "discordInstanceId":"1579527570573582336"
                    }
            }
            """
            response = requests.post(url, headers=headers, data=payload)
            result = response.json()
            logger.debug(f"Imagine response: {result}")
            return result.get("result", None)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during Imagine: {e}")
            raise

    def upscale_or_vary(self, task_id="", action="U1") -> str:
        """
        return subtask_id 
        """
        try:
            logger.debug(f"Upscale/Vary with task_id: {task_id}, action: {action}")
            _, _, buttos = self.sync_mj_status(task_id)
            logger.debug(f"Upscale/Vary with buttons: {buttos}")
            custom_id = buttos[action] 
            url = f"{self.api_url}/mj/submit/action"
            payload = json.dumps({
                "chooseSameChannel": True,
                "customId": custom_id,
                "taskId": task_id,
                "notifyHook": "",
                "state": ""
            })
            headers = {
                'Authorization': 'Bearer {}'.format(self.api_key),
                'Content-Type': 'application/json; charset=utf-8'
            }
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Upscale/Vary response: {result}")
            return result.get("result", None)
        except Exception as e:
            logger.error(f"Error during Upscale/Vary: {e}")
            raise

    def sync_mj_status(self, task_id):
        """
        return image, task_id, buttons 
        """
        try:
            while True:
                url = f"{self.api_url}/mj/task/{task_id}/fetch"
                headers = {
                    'Authorization': 'Bearer {}'.format(self.api_key),
                    'Content-Type': 'application/json; charset=utf-8'
                }
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Fetch response: {data}")
                status = data['status']
                if status == 'SUCCESS':
                    img = None
                    if 'imageUrl' in data:
                        img = self.download_image(data['imageUrl'])
                    if 'buttons' in data:
                        buttons = {}
                        for button in data['buttons']:
                            # Example: actions = { "U1": "MJ::JOB::upsample::1::2452c896-1085-4ac3-b3fe-276e86207480" }
                            buttons[button['label']] = button['customId']
                    return img, task_id, buttons
                elif status == 'FAILED':
                    raise Exception(f"Task failed: {data.get('failReason', 'Unknown error')}")
                elif status in ['', 'SUBMITTED', 'IN_PROGRESS', 'NOT_START']:
                    logger.info(f"Task status: {status}, progress: {data.get('progress', 'Unknown')}")
                    time.sleep(3)  # Wait for 3 seconds before checking again
                else:
                    raise Exception(f"Unknown task status: {data['status']}") 
        except Exception as e:
            logger.error(f"Error during sync_mj_status: {e}")
            raise

    def download_image(self, url):
        logger.debug(f"Downloading image from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return np.array(img)
        except Exception as e:
            logger.error(f"Error downloading image from URL {url}: {str(e)}")
            raise

