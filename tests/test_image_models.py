"""Offline contracts: model options, wire requests, legacy defaults, image decoding."""
import base64
import importlib
import json
from io import BytesIO
from pathlib import Path
import sys
import types
from unittest.mock import Mock

import pytest
import torch
from PIL import Image

# Load node modules without executing ComfyUI's plugin registration entry point.
PACKAGE = 'model_test_plugin'
package = types.ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).resolve().parents[1])]
sys.modules[PACKAGE] = package
utils = types.ModuleType(f'{PACKAGE}.utils')
utils.load_config = lambda: None
utils.init_logger = Mock
sys.modules[utils.__name__] = utils
options = importlib.import_module(f'{PACKAGE}.image_model_options')
responses = importlib.import_module(f'{PACKAGE}.image_response')


def png():
    buffer = BytesIO()
    Image.new('RGB', (2, 2), (255, 0, 0)).save(buffer, format='PNG')
    return buffer.getvalue()


def test_gpt_capabilities():
    for model in options.GPT_25_MODELS:
        options.validate_gpt_options(model, 10, 'max', '3840x2160')
    for model in options.GPT_MODELS[:3]:
        options.validate_gpt_options(model, 1, 'auto', 'auto')
        with pytest.raises(ValueError):
            options.validate_gpt_options(model, 1, 'xhigh', 'auto')
        with pytest.raises(ValueError):
            options.validate_gpt_options(model, 1, 'auto', '2048x2048')
    for n in (0, 11, True, 1.5):
        with pytest.raises(ValueError):
            options.validate_gpt_options(options.GPT_MODELS[0], n, 'auto', 'auto')


def test_gemini_capabilities():
    options.validate_gemini_options(options.GEMINI_MODELS[0], '16:9', '2K')
    options.validate_gemini_options(options.GEMINI_MODELS[1], '16:9', '1K')
    with pytest.raises(ValueError, match='only 1K'):
        options.validate_gemini_options(options.GEMINI_MODELS[1], '16:9', '2K')


def test_response_formats(monkeypatch):
    result = Mock(content=png())
    get = Mock(return_value=result)
    monkeypatch.setattr(responses.requests, 'get', get)
    batch = responses.decode_gpt_images({'data': [
        {'b64_json': base64.b64encode(png()).decode()},
        {'url': 'https://example.com/image.png'},
    ]})
    assert batch.shape == (2, 2, 2, 3)
    assert torch.equal(batch[0], batch[1])
    assert batch[0, 0, 0].tolist() == [1.0, 0.0, 0.0]
    get.assert_called_once_with('https://example.com/image.png', timeout=120)
    with pytest.raises(ValueError):
        responses.download_image('file:///etc/passwd')
    for data in ({}, {'data': []}, {'data': [{}]}):
        with pytest.raises(RuntimeError):
            responses.decode_gpt_images(data)


@pytest.mark.parametrize('editing', [False, True])
def test_gpt_wire_requests(monkeypatch, editing):
    module = importlib.import_module(f'{PACKAGE}.gpt_image_{"edit" if editing else "generate"}_node')
    cls = module.GPTImageEditNode if editing else module.GPTImageGenerateNode
    node = cls.__new__(cls)
    node.logger, node.api_key, node.base_url = Mock(), 'test-token', 'https://example.com/v1'
    response = Mock()
    response.json.return_value = {'data': [{'b64_json': base64.b64encode(png()).decode()}]}
    post = Mock(return_value=response)
    monkeypatch.setattr(module.requests, 'post', post)
    method = node.edit if editing else node.generate
    args = {'image1': torch.zeros(1, 2, 2, 3)} if editing else {}
    for model in options.GPT_MODELS:
        result = method('test', model=model, **args)
        payload = post.call_args.kwargs['data']
        payload = payload if editing else json.loads(payload)
        assert payload['model'] == model
        assert ('response_format' in payload) == (not editing or model not in options.GPT_25_MODELS)
        assert result[0].shape == (1, 2, 2, 3)
    method('test', **args)
    payload = post.call_args.kwargs['data']
    payload = payload if editing else json.loads(payload)
    assert payload['model'] == 'gpt-image-1.5'
    method('test', model='gpt-image-2.5-flare', quality='max', size='3840x2160', **args)
    payload = post.call_args.kwargs['data']
    payload = payload if editing else json.loads(payload)
    assert payload['quality'] == 'max' and payload['size'] == '3840x2160'
    before = post.call_count
    with pytest.raises(ValueError):
        method('test', model='gpt-image-1', quality='max', **args)
    assert post.call_count == before


@pytest.mark.parametrize('editing', [False, True])
def test_gemini_wire_and_legacy_defaults(monkeypatch, editing):
    module = importlib.import_module(f'{PACKAGE}.gemini_image_{"edit" if editing else "generate"}_node')
    cls = module.GeminiImageEditNode if editing else module.GeminiImageGenerateNode
    node = cls.__new__(cls)
    node.logger, node.api_key, node.api_url = Mock(), 'test-token', 'https://example.com'
    response = Mock()
    response.json.return_value = {'candidates': [{'content': {'parts': [
        {'inlineData': {'data': base64.b64encode(png()).decode()}}
    ]}}]}
    post = Mock(return_value=response)
    monkeypatch.setattr(module.requests, 'post', post)
    method = node.edit if editing else node.generate
    args = {'image': torch.zeros(1, 2, 2, 3)} if editing else {}
    for model in [None, options.GEMINI_MODELS[1]]:
        kwargs = {} if model is None else {'model': model}
        assert method('test', **args, **kwargs)[0].shape == (1, 2, 2, 3)
        expected = model or options.GEMINI_MODELS[0]
        assert post.call_args.args[0] == f'https://example.com/v1beta/models/{expected}:generateContent'
        assert post.call_args.kwargs['timeout'] == 180
    before = post.call_count
    with pytest.raises(ValueError):
        method('test', model=options.GEMINI_MODELS[1], image_size='2K', **args)
    assert post.call_count == before


@pytest.mark.parametrize('key', ['inlineData', 'inline_data'])
def test_gemini_response_formats(key):
    result = responses.decode_gemini_images({'candidates': [{'content': {'parts': [
        {'text': 'description'}, {key: {'data': base64.b64encode(png()).decode()}}
    ]}}]})
    assert result.shape == (1, 2, 2, 3)
    for data in ({}, {'candidates': []}, {'candidates': [{'content': {'parts': []}}]}):
        with pytest.raises(RuntimeError):
            responses.decode_gemini_images(data)
