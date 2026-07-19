import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

PROVIDER_PRESETS = {
    "Groq (free)": "https://api.groq.com/openai/v1",
    "OpenRouter (free models)": "https://openrouter.ai/api/v1",
    "Google Gemini (OpenAI-compatible)": "https://generativelanguage.googleapis.com/v1beta/openai",
    "Ollama (local, no key needed)": "http://localhost:11434/v1",
    "Custom": "",
}

DEFAULT_MODEL = "llama-3.1-8b-instant"

VALID_CATEGORIES = ("Technical", "Billing", "Logistics", "Feedback")
VALID_PRIORITIES = ("High", "Medium", "Low")

# Groq hosts a free, fast Whisper endpoint on the same OpenAI-compatible base URL
# used for chat completions, so Speech-to-Text defaults to it out of the box.
DEFAULT_STT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_STT_MODEL = "whisper-large-v3-turbo"

# Text-to-Speech also runs on Groq's OpenAI-compatible endpoint, so one free Groq
# key covers chat completions, Whisper transcription, and speech synthesis.
# Note: Orpheus requires a one-time terms acceptance in the Groq console before use.
DEFAULT_TTS_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_TTS_MODEL = "canopylabs/orpheus-v1-english"

# Voices accepted by canopylabs/orpheus-v1-english (verified against the live API).
GROQ_TTS_VOICES = ("autumn", "diana", "hannah", "austin", "daniel", "troy")
DEFAULT_TTS_VOICE = "autumn"

# Orpheus currently returns WAV only — the API rejects mp3/flac with a 400.
DEFAULT_TTS_FORMAT = "wav"
DEFAULT_EDGE_TTS_VOICE = "en-US-AriaNeural"


@dataclass
class Settings:
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    request_timeout: int
    temperature: float
    max_tokens: int
    stt_api_key: str
    stt_base_url: str
    stt_model: str
    tts_api_key: str
    tts_base_url: str
    tts_model: str
    tts_voice: str
    tts_format: str
    edge_tts_voice: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_base_url=os.getenv("LLM_BASE_URL", PROVIDER_PRESETS["Groq (free)"]),
            llm_model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
            request_timeout=int(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "400")),
            # `or` rather than a getenv default: a key present but blank in .env
            # (as shipped in .env.example) must still fall back to the LLM key.
            stt_api_key=os.getenv("STT_API_KEY") or os.getenv("LLM_API_KEY", ""),
            stt_base_url=os.getenv("STT_BASE_URL", DEFAULT_STT_BASE_URL),
            stt_model=os.getenv("STT_MODEL", DEFAULT_STT_MODEL),
            tts_api_key=os.getenv("TTS_API_KEY") or os.getenv("LLM_API_KEY", ""),
            tts_base_url=os.getenv("TTS_BASE_URL", DEFAULT_TTS_BASE_URL),
            tts_model=os.getenv("TTS_MODEL", DEFAULT_TTS_MODEL),
            tts_voice=os.getenv("TTS_VOICE", DEFAULT_TTS_VOICE),
            tts_format=os.getenv("TTS_FORMAT", DEFAULT_TTS_FORMAT),
            edge_tts_voice=os.getenv("EDGE_TTS_VOICE", DEFAULT_EDGE_TTS_VOICE),
        )


settings = Settings.from_env()
