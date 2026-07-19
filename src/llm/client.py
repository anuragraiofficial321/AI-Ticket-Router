import requests
from config.settings import settings as default_settings
from helpers.json_utils import extract_json, normalize_result
from llm.prompts import SYSTEM_PROMPT, build_user_prompt
from llm.fallback import classify_offline


class LLMClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None,
                 timeout: int = None, temperature: float = None, max_tokens: int = None):
        self.api_key = api_key if api_key is not None else default_settings.llm_api_key
        self.base_url = (base_url or default_settings.llm_base_url).rstrip("/")
        self.model = model or default_settings.llm_model
        self.timeout = timeout or default_settings.request_timeout
        self.temperature = temperature if temperature is not None else default_settings.temperature
        self.max_tokens = max_tokens or default_settings.max_tokens

    def is_configured(self) -> bool:
        return bool(self.api_key) or "localhost" in self.base_url or "127.0.0.1" in self.base_url

    def _call_api(self, ticket_text: str) -> dict:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(ticket_text)},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        return extract_json(raw_text)

    def analyze(self, ticket_text: str) -> dict:
        if not self.is_configured():
            result = classify_offline(ticket_text)
            result["error"] = "No LLM API key configured. Using offline fallback classifier."
            return result

        try:
            parsed = self._call_api(ticket_text)
            return normalize_result(parsed, ticket_text, source="llm")
        except Exception as exc:
            result = classify_offline(ticket_text)
            result["error"] = f"LLM call failed ({exc}). Using offline fallback classifier."
            return result
