import streamlit as st
from config.settings import settings, PROVIDER_PRESETS, GROQ_TTS_VOICES
from llm.client import LLMClient
from audio.stt_client import STTClient
from audio.tts_client import TTSClient


def render_sidebar() -> LLMClient:
    with st.sidebar:
        st.header("⚙️ LLM Settings")
        st.caption("Bring your own free API key. Nothing is stored server-side, only in this session.")

        provider = st.selectbox("Provider", list(PROVIDER_PRESETS.keys()), index=0)
        default_base_url = PROVIDER_PRESETS[provider] or settings.llm_base_url
        base_url = st.text_input("Base URL", value=default_base_url)

        model = st.text_input(
            "Model name",
            value=settings.llm_model,
            help="e.g. llama-3.1-8b-instant (Groq), meta-llama/llama-3.1-8b-instruct:free "
                 "(OpenRouter), gemini-2.0-flash (Gemini), llama3 (Ollama)",
        )

        api_key = st.text_input(
            "API key", value=settings.llm_api_key, type="password",
            help="Leave blank for a local Ollama server.",
        )

        st.markdown("---")
        st.markdown(
            "**Free API key sources:**\n"
            "- [Groq Console](https://console.groq.com/keys) — fast, generous free tier\n"
            "- [OpenRouter](https://openrouter.ai/models?max_price=0) — free-tagged models\n"
            "- [Google AI Studio](https://aistudio.google.com/apikey) — Gemini free tier\n"
            "- [Ollama](https://ollama.com) — run a model locally, no key needed"
        )

    return LLMClient(api_key=api_key, base_url=base_url, model=model)


def render_audio_sidebar(llm_api_key: str = "") -> tuple:
    with st.sidebar:
        st.markdown("---")
        st.header("🎙️ Audio Settings")
        st.caption("Optional: talk to the app and hear replies read aloud. Both work fully free.")

        with st.expander("Speech-to-Text (voice ticket input)", expanded=False):
            st.caption("Powered by Groq's free Whisper endpoint by default.")
            stt_base_url = st.text_input("STT Base URL", value=settings.stt_base_url, key="stt_base_url")
            stt_model = st.text_input("STT Model", value=settings.stt_model, key="stt_model")
            stt_api_key = st.text_input(
                "STT API key", value=llm_api_key or settings.stt_api_key, type="password",
                key="stt_api_key",
                help="Reuses your Groq key from LLM Settings if left as-is. "
                     "Get a free key at https://console.groq.com/keys",
            )

        with st.expander("Text-to-Speech (listen to responses)", expanded=False):
            st.caption(
                "Uses Groq's speech endpoint with your Groq key, and falls back to a "
                "free, no-key Microsoft Edge neural voice automatically."
            )
            tts_api_key = st.text_input(
                "TTS API key", value=llm_api_key or settings.tts_api_key, type="password",
                key="tts_api_key",
                help="Reuses your Groq key from LLM Settings if left as-is. "
                     "Leave blank to always use the free fallback voice.",
            )
            tts_base_url = st.text_input("TTS Base URL", value=settings.tts_base_url, key="tts_base_url")
            tts_model = st.text_input(
                "TTS Model", value=settings.tts_model, key="tts_model",
                help="Groq TTS models require a one-time terms acceptance at "
                     "https://console.groq.com/playground before they can be called.",
            )
            voices = list(GROQ_TTS_VOICES)
            tts_voice = st.selectbox(
                "Voice", voices,
                index=voices.index(settings.tts_voice) if settings.tts_voice in voices else 0,
                key="tts_voice",
                help="Voices supported by the Orpheus model.",
            )
            # Orpheus returns WAV only; offering other formats would silently
            # fail the Groq call and drop every request to the fallback voice.
            tts_format = settings.tts_format
            edge_voice = st.text_input(
                "Fallback voice (no key needed)", value=settings.edge_tts_voice, key="edge_tts_voice",
                help="e.g. en-US-AriaNeural, en-GB-SoniaNeural, en-US-GuyNeural",
            )

    stt_client = STTClient(api_key=stt_api_key, base_url=stt_base_url, model=stt_model)
    tts_client = TTSClient(
        api_key=tts_api_key, base_url=tts_base_url, model=tts_model,
        voice=tts_voice, response_format=tts_format, edge_voice=edge_voice,
    )
    return stt_client, tts_client
