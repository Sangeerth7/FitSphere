import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    """Base error for local Ollama communication or response failures."""


class OllamaUnavailableError(OllamaError):
    """Raised when Ollama cannot be reached or times out."""


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an unusable response."""


def generate_json(prompt, model=None, base_url=None, timeout=None):
    """Call Ollama's local generate API and return its JSON response."""
    model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
    timeout = timeout or float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }).encode("utf-8")
    request = Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise OllamaUnavailableError("Ollama is unavailable.") from error

    try:
        envelope = json.loads(body)
        response_text = envelope.get("response", envelope)
        if isinstance(response_text, str):
            return json.loads(response_text)
        if isinstance(response_text, dict):
            return response_text
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise OllamaResponseError("Ollama returned invalid JSON.") from error

    raise OllamaResponseError("Ollama returned an invalid response shape.")
