import streamlit as st
from db import store
from ui.theme import inject_css
from ui.login import render_login_gate, render_account_sidebar
from ui.sidebar import render_sidebar, render_audio_sidebar
from ui.single_ticket import render_single_ticket_tab
from ui.bulk_upload import render_bulk_upload_tab
from ui.dashboard import render_dashboard_tab

st.set_page_config(page_title="Ticket Triage Engine", page_icon="🎫", layout="wide")

inject_css()
store.init_db()
user = render_login_gate()

if "last_result" not in st.session_state:
    st.session_state.last_result = None

render_account_sidebar(user)
client = render_sidebar()
stt_client, tts_client = render_audio_sidebar(llm_api_key=client.api_key)

st.markdown(
    '<h1 style="margin-bottom:0.15rem">🎫 Intelligent Ticket Router</h1>'
    '<p class="tr-hero-sub">LLM-powered classification, priority scoring and response drafting — '
    "with voice input and audio replies.</p>",
    unsafe_allow_html=True,
)

if not client.is_configured():
    st.warning(
        "No LLM API key configured — running on the offline rule-based fallback classifier. "
        "Add a free API key in the sidebar to enable full LLM triage."
    )

tab1, tab2, tab3 = st.tabs(["Single Ticket", "Bulk Upload", "Dashboard"])

with tab1:
    render_single_ticket_tab(client, stt_client, tts_client, user)

with tab2:
    render_bulk_upload_tab(client, user)

with tab3:
    render_dashboard_tab(user)
