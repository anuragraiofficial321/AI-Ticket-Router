import pandas as pd
import streamlit as st
from llm.client import LLMClient
from helpers.ui_helpers import add_to_history


def render_bulk_upload_tab(client: LLMClient, user: dict) -> None:
    st.markdown("### Bulk Ticket Upload")
    st.markdown(
        '<p class="tr-hero-sub">Upload a CSV with a single column named <code>text</code> '
        "containing raw ticket messages.</p>",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

    if uploaded_file is None:
        return

    bulk_df = pd.read_csv(uploaded_file)
    if "text" not in bulk_df.columns:
        st.error("CSV must contain a 'text' column.")
        return

    progress = st.progress(0, text="Processing tickets...")
    results = []
    total = len(bulk_df)
    for i, msg in enumerate(bulk_df["text"].astype(str)):
        result = client.analyze(msg)
        results.append({
            "text": msg,
            "category": result["category"],
            "priority": result["priority"],
            "confidence": result["confidence"],
            "summary": result.get("summary", ""),
            "suggested_response": result.get("suggested_response", ""),
            "source": result.get("source", "unknown"),
        })
        progress.progress((i + 1) / total, text=f"Processed {i + 1}/{total} tickets...")
    progress.empty()

    results_df = pd.DataFrame(results)
    st.success(f"Processed {len(results_df)} tickets — saved to your history.")

    m1, m2, m3 = st.columns(3)
    m1.metric("Tickets", len(results_df))
    m2.metric("High Priority", int((results_df["priority"] == "High").sum()))
    m3.metric("Avg Confidence", f'{results_df["confidence"].mean():.0f}%')

    st.dataframe(
        results_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "text": st.column_config.TextColumn("Ticket", width="large"),
            "confidence": st.column_config.ProgressColumn(
                "Confidence", min_value=0, max_value=100, format="%d%%"
            ),
            "suggested_response": st.column_config.TextColumn("Suggested Response", width="large"),
        },
    )

    for row in results:
        add_to_history(user["id"], row["text"], row)

    csv_out = results_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️  Download Results as CSV", csv_out, "triage_results.csv", "text/csv")
