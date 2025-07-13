# chat.py  – Streamlit UI + Azure AI Foundry agent via DefaultAzureCredential
# ---------------------------------------------------------------------------
"""
Required secrets in Settings → Secrets  (nothing else):

AI_ENDPOINT  = "https://<foundry-name>.services.ai.azure.com"
PROJECT_NAME = "<your-project-name>"
AGENT_ID     = "asst_0123456789abcdef"
"""

import os, time, streamlit as st
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
from azure.core.exceptions import HttpResponseError

# ---------------------------------------------------------------------------
# 1.  Streamlit page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SME Underwriting AI Agent", page_icon="🤖")
st.title("SME UK Underwriting AI Agent")

# ---------------------------------------------------------------------------
# 2.  Grab Foundry IDs from secrets (abort early if missing)
# ---------------------------------------------------------------------------
try:
    ENDPOINT  = os.environ["AI_ENDPOINT"].rstrip("/")
    PROJECT   = os.environ["PROJECT_NAME"]
    AGENT_ID  = os.environ["AGENT_ID"]
except KeyError as miss:
    st.error(f"Missing secret: {miss}.  Add it in  Settings → Secrets.")
    st.stop()

# ---------------------------------------------------------------------------
# 3.  Cached Azure client using *DefaultAzureCredential*
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="🔑 Authenticating with Azure…")
def get_agent_client():
    cred = DefaultAzureCredential()

    # this will raise if the identity has no token source
    client = AIProjectClient(
        credential=cred,
        endpoint=f"{ENDPOINT}/api/projects/{PROJECT}"
    )
    agent  = client.agents.get_agent(AGENT_ID)  # raises if IDs mismatch / no RBAC
    return client, agent

# ---------------------------------------------------------------------------
# 4.  Helper: send a prompt → get assistant reply
# ---------------------------------------------------------------------------
def ask_agent(prompt: str) -> str:
    client, agent = get_agent_client()

    # (a) create a thread
    th = client.agents.threads.create()

    # (b) post user message
    client.agents.messages.create(th.id, role="user", content=prompt)

    # (c) run the agent
    run = client.agents.runs.create(th.id, agent.id)

    # simple poll (max 60 s)
    for _ in range(60):
        run = client.agents.runs.get(th.id, run.id)
        if run.status in ("succeeded", "failed"):
            break
        time.sleep(1)

    if run.status == "failed":
        raise RuntimeError(run.last_error["message"])

    # (d) read assistant reply
    msgs = client.agents.messages.list(
        th.id, order=ListSortOrder.ASCENDING, limit=20
    )
    for m in reversed(msgs):
        if m.role == "assistant" and m.text_messages:
            return m.text_messages[-1].text.value
    return "(no reply)"

# ---------------------------------------------------------------------------
# 5.  Streamlit chat interface
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# replay history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input("Ask the agent …")

if user_prompt:
    st.session_state.history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                reply = ask_agent(user_prompt)
            except HttpResponseError as e:
                reply = f"⚠️ Azure error:\n```\n{e.message}\n```"
            except Exception as e:
                reply = f"⚠️ {e}"
        st.markdown(reply)

    st.session_state.history.append({"role": "assistant", "content": reply})
