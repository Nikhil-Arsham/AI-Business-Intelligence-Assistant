"""Streamlit user interface for the sales BI assistant."""
import requests
import streamlit as st

st.set_page_config(page_title="AI Business Intelligence Assistant", page_icon="📊", layout="wide")
API_URL = "http://127.0.0.1:5000"

st.title("📊 Mini AI Business Intelligence Assistant")
st.caption("Ask questions about the supplied sales transactions in everyday language.")

try:
    summary = requests.get(f"{API_URL}/api/summary", timeout=3).json()
    c1, c2 = st.columns(2)
    c1.metric("Valid completed transactions", summary["transactions"])
    c2.metric("Total revenue", f"₹{summary['revenue']:,.2f}")
except requests.RequestException:
    st.warning("Backend is not reachable. Start Flask in a separate terminal first.")

st.subheader("Ask a business question")
examples = [
    "What is the total revenue?",
    "Which product generated the highest revenue?",
    "What is the monthly revenue trend?",
    "Which region generated the highest sales?",
    "How did revenue change between January and February?"
]
question = st.text_input("Enter your question", placeholder="e.g. Which region generated the highest sales?")
with st.expander("Example questions"):
    for example in examples:
        st.write(f"• {example}")

ask_clicked = st.button("Ask", type="primary")
if ask_clicked and question.strip():
    try:
        response = requests.post(f"{API_URL}/api/ask", json={"question": question}, timeout=10)
        data = response.json()
        if response.status_code != 200:
            st.error(data.get("error", "The request could not be processed."))
        else:
            st.subheader("Answer")
            st.write(data["answer"])
            rows = data.get("supporting_data", [])
            if rows:
                st.subheader("Supporting figures")
                st.dataframe(rows, use_container_width=True)
                if data.get("intent") == "monthly_trend":
                    st.bar_chart({row["month"]: row["revenue"] for row in rows})
                elif data.get("intent") in ("top_product", "top_region"):
                    label = "product" if data["intent"] == "top_product" else "region"
                    st.bar_chart({row[label]: row["revenue"] for row in rows})
            if data.get("intent") == "unsupported":
                st.info("Try one of the supported example questions.")
    except requests.RequestException:
        st.error("Could not connect to the backend. Make sure Flask is running.")
elif ask_clicked and not question.strip():
    st.warning("Please enter a question.")

st.divider()
st.caption("Data policy: only completed transactions with valid required values and positive quantities are included.")
