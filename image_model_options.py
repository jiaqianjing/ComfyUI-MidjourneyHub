"""Model capabilities. Inputs: model/options; output: None; invalid options raise.

Validation is deterministic and has no I/O or mutation. Model IDs are Yunwu IDs.
"""

GPT_MODELS = ['gpt-image-2-all', 'gpt-image-1.5', 'gpt-image-1',
              'gpt-image-2.5-flare', 'gpt-image-2.5-sunburst']
GPT_25_MODELS = frozenset(GPT_MODELS[-2:])
GPT_QUALITIES = ['auto', 'high', 'medium', 'low', 'xhigh', 'max']
GPT_SIZES = ['auto', '1024x1024', '1536x1024', '1024x1536',
             '2048x2048', '2048x1152', '3840x2160', '2160x3840']
GEMINI_MODELS = ['gemini-3-pro-image-preview', 'gemini-3.1-flash-lite-image']
GEMINI_SIZES = {'gemini-3-pro-image-preview': ('1K', '2K'),
                'gemini-3.1-flash-lite-image': ('1K',)}
ASPECT_RATIOS = ['1:1', '9:16', '16:9', '4:3', '3:4']


def validate_gpt_options(model, n, quality, size, *, editing=False):
    """Validate options before network I/O; preserve legacy DALL-E edit options."""
    if model not in GPT_MODELS + (['dall-e-2'] if editing else []):
        raise ValueError(f'Unknown GPT image model: {model}')
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 10:
        raise ValueError('n must be an integer from 1 to 10')
    if quality not in GPT_QUALITIES or size not in GPT_SIZES:
        raise ValueError('Unsupported image quality or size')
    if model not in GPT_25_MODELS:
        if quality in ('xhigh', 'max') or size in GPT_SIZES[4:]:
            raise ValueError('xhigh/max and large sizes require GPT Image 2.5')


def validate_gemini_options(model, aspect_ratio, image_size):
    """Reject unknown models and resolutions unsupported by the selected model."""
    if model not in GEMINI_SIZES:
        raise ValueError(f'Unknown Gemini image model: {model}')
    if aspect_ratio not in ASPECT_RATIOS:
        raise ValueError('Unsupported aspect ratio')
    if image_size not in GEMINI_SIZES[model]:
        raise ValueError(f'{model} supports only {", ".join(GEMINI_SIZES[model])}')
