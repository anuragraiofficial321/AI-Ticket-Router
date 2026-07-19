import streamlit as st

PRIORITY_STYLES = {
    "High": ("#b42318", "#fef3f2", "#fecdca"),
    "Medium": ("#b54708", "#fffaeb", "#fedf89"),
    "Low": ("#067647", "#ecfdf3", "#abefc6"),
}

CATEGORY_ICONS = {
    "Technical": "🛠️",
    "Billing": "💳",
    "Logistics": "📦",
    "Feedback": "💬",
}

CSS = """
<style>
:root {
    --tr-border: #e4e7ec;
    --tr-muted: #667085;
    --tr-accent: #4f46e5;
}

/* Roomier, centred page with a consistent max width */
.block-container {
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    max-width: 1180px;
}

h1, h2, h3 { letter-spacing: -0.02em; font-weight: 650; }
h1 { font-size: 1.9rem !important; }

/* Sidebar reads as a quieter panel than the main canvas */
[data-testid="stSidebar"] {
    background: #fbfbfd;
    border-right: 1px solid var(--tr-border);
}
[data-testid="stSidebar"] h2 { font-size: 1.05rem !important; }

/* Metrics as cards instead of naked numbers */
[data-testid="stMetric"] {
    background: #fff;
    border: 1px solid var(--tr-border);
    border-radius: 12px;
    padding: 1rem 1.1rem;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
[data-testid="stMetricLabel"] p {
    font-size: 0.78rem !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--tr-muted);
}
[data-testid="stMetricValue"] { font-size: 1.4rem !important; }

/* Tabs: underline style rather than boxed */
.stTabs [data-baseweb="tab-list"] {
    gap: 1.75rem;
    border-bottom: 1px solid var(--tr-border);
}
.stTabs [data-baseweb="tab"] {
    padding: 0.6rem 0;
    font-weight: 550;
    color: var(--tr-muted);
}
.stTabs [aria-selected="true"] { color: var(--tr-accent); }

/* Buttons and inputs share one radius and a calmer border */
.stButton button, .stDownloadButton button, .stFormSubmitButton button {
    border-radius: 8px;
    font-weight: 550;
    padding: 0.45rem 1.1rem;
    transition: transform 0.05s ease, box-shadow 0.15s ease;
}
.stButton button:active, .stFormSubmitButton button:active { transform: translateY(1px); }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: 8px;
}

/* Expanders and forms as light cards */
[data-testid="stExpander"] details {
    border: 1px solid var(--tr-border);
    border-radius: 12px;
    background: #fff;
}
[data-testid="stForm"] {
    border: 1px solid var(--tr-border);
    border-radius: 14px;
    padding: 1.4rem;
    background: #fff;
    box-shadow: 0 1px 3px rgba(16, 24, 40, 0.05);
}

[data-testid="stDataFrame"] { border-radius: 10px; }
footer, #MainMenu { visibility: hidden; }

/* Shared building blocks used by the tabs below */
.tr-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    border: 1px solid transparent;
}
.tr-card {
    border: 1px solid var(--tr-border);
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
    background: #fff;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
.tr-card-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--tr-muted);
    margin-bottom: 0.45rem;
}
.tr-hero-sub { color: var(--tr-muted); font-size: 0.98rem; margin-top: -0.4rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def priority_badge(priority: str) -> str:
    color, bg, border = PRIORITY_STYLES.get(priority, ("#344054", "#f2f4f7", "#e4e7ec"))
    return (
        f'<span class="tr-badge" style="color:{color};background:{bg};border-color:{border}">'
        f"{priority} priority</span>"
    )


def card(label: str, body: str) -> str:
    return f'<div class="tr-card"><div class="tr-card-label">{label}</div>{body}</div>'
