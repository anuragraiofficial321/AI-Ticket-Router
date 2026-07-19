import streamlit as st
from db import store


def render_login_gate() -> dict:
    """Show sign in / sign up until authenticated. Returns the logged-in user."""
    user = st.session_state.get("user")
    if user:
        # The account can disappear underneath an open session if the database is
        # reset; without this the next save fails on a raw FOREIGN KEY error.
        if store.user_exists(user["id"]):
            return user
        st.session_state.pop("user", None)
        st.warning("Your session expired because the account no longer exists. Please sign in again.")

    # Narrow centre column keeps the auth form from stretching across the page.
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown(
            '<div style="text-align:center;margin-bottom:1.5rem">'
            '<div style="font-size:2.6rem;line-height:1">🎫</div>'
            '<h1 style="margin:0.4rem 0 0.2rem">Ticket Triage Engine</h1>'
            '<p class="tr-hero-sub">Sign in to keep your own private triage history.</p>'
            "</div>",
            unsafe_allow_html=True,
        )

        sign_in_tab, sign_up_tab = st.tabs(["Sign In", "Create Account"])

        with sign_in_tab:
            with st.form("sign_in_form"):
                username = st.text_input("Username", placeholder="your username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                if st.form_submit_button("Sign In", type="primary", use_container_width=True):
                    result = store.verify_user(username, password)
                    if result.get("error"):
                        st.error(result["error"])
                    else:
                        st.session_state.user = result["user"]
                        st.rerun()

        with sign_up_tab:
            with st.form("sign_up_form"):
                new_username = st.text_input("Choose a username", placeholder="at least 3 characters")
                new_password = st.text_input(
                    "Choose a password", type="password", placeholder="at least 6 characters"
                )
                confirm = st.text_input("Confirm password", type="password", placeholder="repeat it")
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if new_password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        result = store.create_user(new_username, new_password)
                        if result.get("error"):
                            st.error(result["error"])
                        else:
                            st.session_state.user = result["user"]
                            st.rerun()

        st.caption(
            "Your history is stored locally in this app's database and is visible only to your account."
        )

    st.stop()


def render_account_sidebar(user: dict) -> None:
    with st.sidebar:
        st.markdown(
            f'<div class="tr-card" style="display:flex;align-items:center;gap:0.7rem">'
            f'<div style="width:36px;height:36px;border-radius:50%;background:#4f46e5;color:#fff;'
            f'display:flex;align-items:center;justify-content:center;font-weight:600">'
            f"{user['username'][0].upper()}</div>"
            f'<div><div style="font-weight:600;line-height:1.2">{user["username"]}</div>'
            f'<div style="font-size:0.78rem;color:#667085">Signed in</div></div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", use_container_width=True):
            for key in ("user", "last_result", "ticket_text_area", "last_audio_digest"):
                st.session_state.pop(key, None)
            st.rerun()
        st.markdown("---")
