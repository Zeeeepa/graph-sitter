from openai import OpenAI

# Handle optional OpenAI dependency
try:
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    class OpenAI:
        def __init__(self, api_key=None):
            self.api_key = api_key
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI not available. Install with: pip install openai")

def get_openai_client(key: str) -> OpenAI:
    return OpenAI(api_key=key)
