from __future__ import annotations
import json
import os
import urllib.error
import urllib.request


class LLMError(RuntimeError):
    pass


def chat_completion(messages: list[dict], config: dict, temperature: float = 0.0) -> str:
    """Call an OpenAI-compatible chat completions endpoint using the standard library."""
    llm_cfg = config.get("llm", {})
    api_key = os.getenv(llm_cfg.get("api_key_env", "LLM_API_KEY"), "")
    base_url = os.getenv(llm_cfg.get("base_url_env", "LLM_BASE_URL"), "").rstrip("/")
    model = os.getenv(llm_cfg.get("model_env", "LLM_MODEL"), "")
    timeout = int(os.getenv(llm_cfg.get("timeout_env", "LLM_TIMEOUT_SECONDS"), "180"))
    if not api_key:
        raise LLMError("Missing API key. Set LLM_API_KEY in your environment or .env.")
    if not base_url or not model:
        raise LLMError("Set LLM_BASE_URL and LLM_MODEL in your environment.")
    url = base_url + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": int(llm_cfg.get("max_output_tokens", 6000)),
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:2000]
        raise LLMError(f"LLM HTTP error {exc.code}: {body}") from exc
    except Exception as exc:
        raise LLMError(f"LLM request failed: {exc}") from exc
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise LLMError(f"Unexpected LLM response schema: {str(data)[:1000]}") from exc
