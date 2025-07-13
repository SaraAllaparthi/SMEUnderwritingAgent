# chat.py
import os, streamlit as st
from azure.identity import ClientSecretCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder

# ---- secrets from Streamlit Cloud ---------------------------------
cred = ClientSecretCredential(
        tenant_id     = os.environ["AZURE_TENANT_ID"],
        client_id     = os.environ["AZURE_CLIENT_ID"],
        client_secret = os.environ["AZURE_CLIENT_SECRET"]
)
endpoint  = os.environ["AI_ENDPOINT"].rstrip("/")
agent_id  = os.environ["AGENT_ID"]

# ---- Foundry client -----------------------------------------------
proj = AIProjectClient(
        credential = cred,
        endpoint   = f"{endpoint}/api/projects/sara-openai-underwritin-project"
)
agent = proj.agents.get_agent(agent_id)

def ask_agent(prompt: str) -> str:
    # 1) create a new thread
    th = proj.agents.threads.create()

    # 2) post user message
    proj.agents.messages.create(thread_id=th.id, role="user", content=prompt)

    # 3) run agent
    run = proj.agents.runs.create_and_process(thread_id=th.id, agent_id=agent.id)
    if run.status == "failed":
        raise RuntimeError(run.last_error["message"])

    # 4) fetch assistant answer
    msgs = proj.agents.messages.list(thread_id=th.id, order=ListSortOrder.ASCENDING)
    return next(m.text_messages[-1].text.value for m in msgs if m.role == "assistant")

# ---- Streamlit UI -------------------------------------------------
st.title("SME Underwriting AI Agent")

q = st.chat_input("Ask the agent…")
if q:
    with st.spinner("Thinking…"):
        try:
            st.markdown(f"> **You:** {q}")
            answer = ask_agent(q)
            st.markdown(f"**Agent:** {answer}")
        except Exception as e:
            st.error(f"⚠️ {e}")
