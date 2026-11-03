"""Decode image responses into ComfyUI RGB batches.

CALLING SPEC: decode_gpt_images(dict) / decode_gemini_images(dict) -> float Tensor [B,H,W,3].
Side effects: downloads URL images without API credentials; raises on bad data.
"""
import base64
from io import BytesIO
from urllib.parse import urlsplit

import numpy as np
from PIL import Image
import requests
import torch


def image_bytes_to_tensor(image_bytes):
    """Bytes -> RGB float HWC tensor; deterministic, no external I/O."""
    with Image.open(BytesIO(image_bytes)) as image:
        return torch.from_numpy(np.array(image.convert('RGB'))).float() / 255.0


def download_image(url):
    """Download an HTTP(S) image; never forward the generation API token."""
    if urlsplit(url).scheme not in ('https', 'http'):
        raise ValueError('Image URL must use HTTP or HTTPS')
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.content


def decode_gpt_images(data):
    """API dict -> RGB batch; accepts b64_json or URL, rejects empty batches."""
    tensors = []
    for item in data.get('data', []):
        if item.get('b64_json'):
            content = base64.b64decode(item['b64_json'], validate=True)
        elif item.get('url'):
            content = download_image(item['url'])
        else:
            raise RuntimeError('Image response contains neither b64_json nor URL')
        tensors.append(image_bytes_to_tensor(content))
    if not tensors:
        raise RuntimeError('No images returned by the image API')
    if len({tuple(t.shape) for t in tensors}) != 1:
        raise RuntimeError('Returned images have different sizes; request an explicit size')
    return torch.stack(tensors, dim=0)


def decode_gemini_images(data):
    """Gemini dict -> RGB batch; deterministic, no network I/O; raises if empty."""
    candidates = data.get('candidates', [])
    parts = candidates[0].get('content', {}).get('parts', []) if candidates else []
    tensors = []
    for part in parts:
        inline = part.get('inlineData') or part.get('inline_data') or {}
        if inline.get('data'):
            tensors.append(image_bytes_to_tensor(base64.b64decode(inline['data'])))
    if not tensors:
        raise RuntimeError('No image data found in API response')
    return torch.stack(tensors, dim=0)
