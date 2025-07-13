import streamlit as st
from chat import ask_agent

st.set_page_config(page_title="SME UW AI Chat", page_icon="🤖")
st.title("SME Underwriting AI Agent 🤖")

prompt = st.chat_input("Ask me something …")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)

    with st.spinner("Thinking…"):
        try:
            answer = ask_agent(prompt)
        except Exception as e:
            answer = f"⚠️ Error: {e}"

    with st.chat_message("assistant"):
        st.write(answer)
