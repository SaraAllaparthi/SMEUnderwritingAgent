import streamlit as st, requests, os, json

API = os.getenv("ASK_URL", "https://white-desert-01e467e03.2.azurestaticapps.net/api/ask")

st.title("SME Underwriting AI Agent")

if "history" not in st.session_state: st.session_state.history = []

q = st.chat_input("Ask the agent…")
if q:
    st.session_state.history.append(("user", q))
    r = requests.post(API, json={"prompt": q}, timeout=120)
    ans = r.json().get("answer", "(error)")
    st.session_state.history.append(("assistant", ans))

for role, msg in st.session_state.history:
    st.chat_message(role).write(msg)
