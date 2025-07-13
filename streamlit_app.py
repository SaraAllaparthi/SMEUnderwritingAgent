import os, streamlit as st
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from azure.ai.agents.models import ListSortOrder

# ---- 1. Secrets from Streamlit --------------------
ENDPOINT = os.environ["AI_ENDPOINT"].rstrip("/")
AGENT_ID = os.environ["AGENT_ID"]
cred     = ClientSecretCredential(
    tenant_id = os.environ["AZURE_TENANT_ID"],
    client_id = os.environ["AZURE_CLIENT_ID"],
    client_secret = os.environ["AZURE_CLIENT_SECRET"]
)

# ---- 2. Azure-Foundry client ----------------------
proj = AIProjectClient(credential=cred, endpoint=f"{ENDPOINT}/api/projects/sara-openai-underwritin-project")
agent = proj.agents.get_agent(AGENT_ID)

# ---- 3. Streamlit UI ------------------------------
st.title("SME Underwriting AI Agent")

prompt = st.chat_input("Ask something…")
if prompt:
    with st.spinner("Thinking…"):
        thread = proj.agents.threads.create()
        proj.agents.messages.create(thread_id=thread.id, role="user", content=prompt)
        run = proj.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

        if run.status == "failed":
            st.error(run.last_error["message"])
        else:
            messages = proj.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
            answer = next((m.text_messages[-1].text.value for m in messages if m.role == "assistant"), "")
            st.markdown(f"**Agent:** {answer}")
