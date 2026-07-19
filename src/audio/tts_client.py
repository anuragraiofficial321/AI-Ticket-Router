import asyncio
import requests
from config.settings import settings as default_settings

MIME_TYPES = {"wav": "audio/wav", "mp3": "audio/mp3", "flac": "audio/flac", "ogg": "audio/ogg"}


class TTSClient:
    """Converts text to speech via Groq's OpenAI-compatible /audio/speech endpoint,
    falling back to Microsoft Edge's free, no-key neural voices (edge-tts) when no
    Groq key is set or the request fails."""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None,
                 voice: str = None, response_format: str = None,
                 edge_voice: str = None, timeout: int = None):
        self.api_key = api_key if api_key is not None else default_settings.tts_api_key
        self.base_url = (base_url or default_settings.tts_base_url).rstrip("/")
        self.model = model or default_settings.tts_model
        self.voice = voice or default_settings.tts_voice
        self.response_format = response_format or default_settings.tts_format
        self.edge_voice = edge_voice or default_settings.edge_tts_voice
        self.timeout = timeout or default_settings.request_timeout

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _synthesize_groq(self, text: str) -> bytes:
        response = requests.post(
            f"{self.base_url}/audio/speech",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "voice": self.voice,
                "input": text,
                "response_format": self.response_format,
            },
            timeout=self.timeout,
        )
        if response.status_code != 200:
            # Groq returns a JSON error body; surface its message rather than raw HTML.
            try:
                message = response.json()["error"]["message"]
            except (ValueError, KeyError):
                message = response.text[:200]
            raise RuntimeError(f"{response.status_code}: {message}")
        return response.content

    def _synthesize_edge_tts(self, text: str) -> bytes:
        import edge_tts

        async def _run() -> bytes:
            communicate = edge_tts.Communicate(text, voice=self.edge_voice)
            audio_chunks = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.extend(chunk["data"])
            return bytes(audio_chunks)

        return asyncio.run(_run())

    def synthesize(self, text: str) -> dict:
        text = (text or "").strip()
        if not text:
            return {"audio": None, "error": "No text to synthesize.", "source": None, "mime": None}

        warning = None
        if self.is_configured():
            try:
                audio = self._synthesize_groq(text)
                mime = MIME_TYPES.get(self.response_format, "audio/wav")
                return {"audio": audio, "error": None, "source": "groq", "mime": mime}
            except Exception as exc:
                warning = f"Groq TTS failed ({exc}) — used the free fallback voice instead."

        try:
            audio = self._synthesize_edge_tts(text)
            # edge-tts always streams MP3 regardless of the Groq format setting.
            return {"audio": audio, "error": warning, "source": "edge-tts", "mime": "audio/mp3"}
        except Exception as exc:
            return {"audio": None, "error": f"Text-to-speech failed: {exc}", "source": None, "mime": None}
