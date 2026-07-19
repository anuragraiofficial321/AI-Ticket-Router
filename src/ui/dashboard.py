import pandas as pd
import streamlit as st
from db import store


def render_dashboard_tab(user: dict) -> None:
    st.markdown("### Triage Dashboard")
    st.markdown(
        f'<p class="tr-hero-sub">Saved history for <b>{user["username"]}</b> — private to this account.</p>',
        unsafe_allow_html=True,
    )

    history = store.get_history(user["id"])
    if not history:
        st.info("No tickets analyzed yet. Use the Single Ticket or Bulk Upload tabs to get started.")
        return

    hist_df = pd.DataFrame(history)
    high_count = int((hist_df["priority"] == "High").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Tickets", len(hist_df))
    k2.metric("High Priority", high_count)
    k3.metric("Avg Confidence", f'{hist_df["confidence"].mean():.0f}%')
    k4.metric("Top Category", hist_df["category"].value_counts().idxmax())

    st.markdown("")
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Tickets by Category**")
        st.bar_chart(hist_df["category"].value_counts(), color="#4f46e5")
    with d2:
        st.markdown("**Tickets by Priority**")
        st.bar_chart(hist_df["priority"].value_counts(), color="#0ea5e9")

    st.markdown("**Full Ticket Log**")
    st.dataframe(
        hist_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "created_at": st.column_config.TextColumn("When", width="small"),
            "text": st.column_config.TextColumn("Ticket", width="large"),
            "confidence": st.column_config.ProgressColumn(
                "Confidence", min_value=0, max_value=100, format="%d%%"
            ),
            "suggested_response": st.column_config.TextColumn("Suggested Response", width="large"),
        },
    )

    a1, a2 = st.columns([1, 3])
    with a1:
        st.download_button(
            "⬇️  Download CSV",
            hist_df.to_csv(index=False).encode("utf-8"),
            f"{user['username']}_ticket_history.csv",
            "text/csv",
            use_container_width=True,
        )
    with a2:
        if st.button("🗑️  Clear My History"):
            store.clear_history(user["id"])
            st.rerun()
