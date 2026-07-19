import hashlib

import streamlit as st
from llm.client import LLMClient
from audio.stt_client import STTClient
from audio.tts_client import TTSClient
from helpers.ui_helpers import source_label, add_to_history
from ui.theme import CATEGORY_ICONS, priority_badge, card

TICKET_KEY = "ticket_text_area"


@st.cache_data(show_spinner=False)
def _synthesize_cached(text: str, api_key: str, base_url: str, model: str,
                       voice: str, response_format: str, edge_voice: str) -> dict:
    """Cached so the reply is spoken once per result, not re-synthesized on every rerun."""
    client = TTSClient(
        api_key=api_key, base_url=base_url, model=model,
        voice=voice, response_format=response_format, edge_voice=edge_voice,
    )
    return client.synthesize(text)


def _handle_recording(stt_client: STTClient) -> None:
    """Transcribe a new recording automatically — no separate button to press."""
    audio_value = st.audio_input(
        "Record the customer's message",
        help="Transcription starts automatically as soon as you stop recording.",
    )
    if audio_value is None:
        return

    raw = audio_value.getvalue()
    digest = hashlib.sha256(raw).hexdigest()
    if digest == st.session_state.get("last_audio_digest"):
        return  # Already transcribed this clip; don't re-spend the API call on reruns.

    st.session_state.last_audio_digest = digest
    with st.spinner("Transcribing your recording..."):
        stt_result = stt_client.transcribe(raw)

    if stt_result["error"]:
        st.warning(stt_result["error"])
        return

    # Write straight into the text area's own state, then rerun so it shows up.
    st.session_state[TICKET_KEY] = stt_result["text"]
    st.rerun()


def render_single_ticket_tab(client: LLMClient, stt_client: STTClient, tts_client: TTSClient, user: dict) -> None:
    st.markdown("### Analyze a Ticket")
    st.markdown(
        '<p class="tr-hero-sub">Type or paste the customer message below — or record it and '
        "it will be transcribed for you automatically.</p>",
        unsafe_allow_html=True,
    )

    with st.expander("🎙️  Record instead of typing", expanded=False):
        _handle_recording(stt_client)

    st.text_area(
        "Customer message",
        height=160,
        key=TICKET_KEY,
        placeholder="e.g. My app keeps crashing every time I try to upload a file, this is urgent!",
        label_visibility="collapsed",
    )

    action, opts = st.columns([1, 2])
    with action:
        analyze_clicked = st.button("Analyze Ticket", type="primary", use_container_width=True)
    with opts:
        st.toggle(
            "🔊 Read the reply aloud automatically", key="autoplay_replies",
            help="Plays the drafted response as soon as the analysis is ready.",
        )

    ticket_text = st.session_state.get(TICKET_KEY, "")

    if analyze_clicked and ticket_text.strip():
        with st.spinner("Analyzing ticket..."):
            result = client.analyze(ticket_text)

        if result.get("error"):
            st.info(result["error"])

        add_to_history(user["id"], ticket_text, result)
        st.session_state.last_result = result
    elif analyze_clicked:
        st.warning("Please enter a ticket message before analyzing.")

    result = st.session_state.get("last_result")
    if not result:
        return

    st.markdown("---")

    category = result["category"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Category", f"{CATEGORY_ICONS.get(category, '🎫')} {category}")
    c2.metric("Priority", result["priority"])
    c3.metric("Confidence", f'{result["confidence"]}%')
    c4.metric("Source", source_label(result.get("source", "unknown")))

    st.markdown(priority_badge(result["priority"]), unsafe_allow_html=True)
    st.progress(min(max(int(result["confidence"]), 0), 100) / 100)

    st.markdown("")
    left, right = st.columns(2)
    with left:
        st.markdown(card("Summary", result.get("summary", "")), unsafe_allow_html=True)
    with right:
        st.markdown(card("Suggested Response", result.get("suggested_response", "")), unsafe_allow_html=True)

    _render_playback(result.get("suggested_response", ""), tts_client)


def _render_playback(reply: str, tts_client: TTSClient) -> None:
    """Audio player is rendered with the result — no click needed to reveal it."""
    if not reply.strip():
        return

    st.markdown("")
    with st.spinner("Preparing audio..."):
        tts_result = _synthesize_cached(
            reply, tts_client.api_key, tts_client.base_url, tts_client.model,
            tts_client.voice, tts_client.response_format, tts_client.edge_voice,
        )

    if not tts_result.get("audio"):
        st.caption(f'🔇 Audio unavailable — {tts_result.get("error", "unknown error")}')
        return

    st.audio(
        tts_result["audio"],
        format=tts_result.get("mime", "audio/wav"),
        autoplay=bool(st.session_state.get("autoplay_replies")),
    )
    voice = "Groq" if tts_result.get("source") == "groq" else "free fallback voice"
    st.caption(f"🔊 Spoken reply · {voice}")
    if tts_result.get("error"):
        st.caption(tts_result["error"])
