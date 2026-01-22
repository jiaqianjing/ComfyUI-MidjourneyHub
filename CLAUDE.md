# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ComfyUI-MidjourneyHub is a custom node extension for ComfyUI that integrates commercial image generation APIs (Midjourney, OpenAI GPT-Image, Google Gemini) through the Yunwu API proxy service.

## Architecture

### Core Components

- **`__init__.py`**: Node registration - defines `NODE_CLASS_MAPPINGS`, `NODE_DISPLAY_NAME_MAPPINGS`, and `__all__` exports for ComfyUI
- **`api_client.py`**: `MJClient` class - async HTTP client for Midjourney API operations (imagine, upscale, vary, blend, status polling)
- **`utils.py`**: Configuration loading from `config.ini` and logging setup with file rotation
- **`config.ini`**: API credentials for different services (MIDJOURNEY_API, GPT_IMAGE_API, GEMINI_API sections)

### Node Implementation Pattern

All nodes follow the ComfyUI custom node convention:
1. `INPUT_TYPES()` classmethod - defines required/optional inputs with types and defaults
2. `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, `CATEGORY` class attributes
3. Main execution method (typically `generate()`) that returns a tuple matching `RETURN_TYPES`
4. All nodes use `CATEGORY = "MidjourneyHub"` for consistent UI organization

Image tensors are returned in ComfyUI format: `torch.Tensor` with shape `(B, H, W, C)`, values normalized to 0-1 range.

### Node Categories

**Midjourney Nodes** (use `MJClient` with async/await):
- `MidjourneyImagineNode` - text-to-image generation
- `MidjourneyActionNode` / `MidjourneyBatchActionNode` - upscale/variation operations
- `MidjourneyBlendNode` - image mixing

**OpenAI Nodes** (use `openai` Python SDK):
- `GPTImageGenerateNode` - gpt-image-1 text-to-image
- `GPTImageEditNode` - gpt-image-1 image editing

**Gemini Nodes** (use `google-genai` SDK with aiohttp):
- `GeminiImageGenerateNode` - Gemini 3 Pro text-to-image
- `GeminiImageEditNode` - Gemini 3 Pro image editing

### Async Pattern (Critical)

ComfyUI now runs nodes in an async context, which causes "This event loop is already running" errors with `loop.run_until_complete()`. This project uses `nest_asyncio` to allow nested event loops.

**All async node files must include this at the top:**

```python
import asyncio

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # nest_asyncio not installed, will use fallback
```

**Then use the standard event loop pattern:**

```python
# Get or create event loop
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

result = loop.run_until_complete(async_method())
```

**Do NOT**:
- Create a new loop every time with `asyncio.new_event_loop()` without checking for existing loop
- Close the loop after use (ComfyUI may be using it)
- Use `asyncio.run()` (incompatible with running event loops)
- Call `asyncio.set_event_loop()` without passing the loop argument
- Forget to add nest_asyncio import at the top of async node files

### Logging

All nodes must use the centralized logger from `utils.py`:

```python
from .utils import init_logger

logger = init_logger()

# Use logger for all output
logger.error(f"Error in NodeName: {str(e)}")
logger.debug(f"Debug info: {data}")
```

**Do NOT**:
- Use `print()` statements for error handling or debugging
- Create separate logger instances per node

### Configuration

API keys and URLs are stored in `config.ini` with sections per service. Do not commit actual API keys.

## Common Issues Fixed

1. **"Event loop already running" error** - ComfyUI now runs nodes in async context. Fixed by adding `nest_asyncio` to all async nodes
2. **asyncio.set_event_loop() missing argument** - Fixed in midjourney_action_node.py:72
3. **Inconsistent event loop handling** - Standardized across all nodes to reuse existing loops
4. **Print statements in production** - Replaced with proper logging
5. **Missing `__all__` export** - Added to `__init__.py` for proper module interface
6. **Inconsistent CATEGORY values** - All nodes now use "MidjourneyHub" category
7. **Unused imports** - Removed unused `json` import from gemini_image_edit_node.py

## Dependencies

This project requires `nest_asyncio` to handle nested event loops in ComfyUI's async environment. Install with:

```bash
pip install nest_asyncio
```

All dependencies are listed in `requirements.txt`.
