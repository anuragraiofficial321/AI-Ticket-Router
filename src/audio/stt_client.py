import requests
from config.settings import settings as default_settings


class STTClient:
    """Transcribes recorded audio to text via any OpenAI-compatible
    /audio/transcriptions endpoint. Defaults to Groq's free, fast
    Whisper-large-v3-turbo model, but any compatible provider works."""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, timeout: int = None):
        self.api_key = api_key if api_key is not None else default_settings.stt_api_key
        self.base_url = (base_url or default_settings.stt_base_url).rstrip("/")
        self.model = model or default_settings.stt_model
        self.timeout = timeout or default_settings.request_timeout

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def transcribe(self, audio_bytes: bytes, filename: str = "ticket.wav") -> dict:
        if not audio_bytes:
            return {"text": "", "error": "No audio was recorded."}

        if not self.is_configured():
            return {
                "text": "",
                "error": "No speech-to-text API key configured. Add a free Groq API key in the "
                         "sidebar (Audio Settings) to enable voice-to-text, or type your ticket manually.",
            }

        url = f"{self.base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {"file": (filename, audio_bytes, "audio/wav")}
        data = {"model": self.model}

        try:
            response = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            text = (result.get("text") or "").strip()
            if not text:
                return {"text": "", "error": "Could not detect any speech in the recording. Please try again."}
            return {"text": text, "error": None}
        except Exception as exc:
            return {"text": "", "error": f"Transcription failed ({exc}). Please type your ticket manually."}
