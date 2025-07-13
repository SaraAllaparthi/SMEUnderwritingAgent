# chat.py  –  one-file Streamlit + Azure AI Foundry agent
# -----------------------------------------------
import os, time, streamlit as st
from azure.identity import ClientSecretCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
from azure.core.exceptions import HttpResponseError

# -----------------------------------------------
# 0.  Streamlit settings
# -----------------------------------------------
st.set_page_config(page_title="SME Underwriting AI Agent",
                   page_icon="🤖",
                   layout="centered")
st.title("SME UK Underwriting AI Agent 🤖")

# -----------------------------------------------
# 1.  Grab secrets from Streamlit Cloud
#     (defined in Settings → Secrets)
# -----------------------------------------------
try:
    ENDPOINT  = os.environ["AI_ENDPOINT"].rstrip("/")
    AGENT_ID  = os.environ["AGENT_ID"]
    TENANT_ID = os.environ["AZURE_TENANT_ID"]
    CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
    SECRET    = os.environ["AZURE_CLIENT_SECRET"]
except KeyError as missing:
    st.error(f"Missing secret: {missing}. "
             "Add it in  Settings → Secrets  and press Rerun.")
    st.stop()

# -----------------------------------------------
# 2.  Create a cached Foundry client + agent
# -----------------------------------------------
@st.cache_resource(show_spinner="🔑 Connecting to Azure AI Foundry …")
def init_agent():
    cred = ClientSecretCredential(
        tenant_id     = TENANT_ID,
        client_id     = CLIENT_ID,
        client_secret = SECRET,
    )

    project_name = "sara-openai-underwritin-project"
    endpoint     = f"{ENDPOINT}/api/projects/{project_name}"

    proj  = AIProjectClient(credential=cred, endpoint=endpoint)
    agent = proj.agents.get_agent(AGENT_ID)   # raises if RBAC missing
    return proj, agent

# -----------------------------------------------
# 3.  Function that sends a prompt to the agent
# -----------------------------------------------
def ask_agent(prompt: str) -> str:
    proj, agent = init_agent()

    # 3-a  create a thread
    thread = proj.agents.threads.create()

    # 3-b  post the user message
    proj.agents.messages.create(thread.id, role="user", content=prompt)

    # 3-c  run the agent and wait
    run = proj.agents.runs.create(thread.id, agent.id)
    # simple poll loop (max 60 s)
    for _ in range(60):
        run = proj.agents.runs.get(thread.id, run.id)
        if run.status in ("succeeded", "failed"): break
        time.sleep(1)

    if run.status == "failed":
        raise RuntimeError(run.last_error["message"])

    # 3-d  fetch assistant reply
    msgs = proj.agents.messages.list(thread.id,
                                     order=ListSortOrder.ASCENDING,
                                     limit=20)
    for m in reversed(msgs):
        if m.role == "assistant" and m.text_messages:
            return m.text_messages[-1].text.value
    return "(no answer)"

# -----------------------------------------------
# 4.  Simple Streamlit chat UI
# -----------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []   # list[dict] with keys: role, content

# render history
for item in st.session_state.history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

# input box
user_msg = st.chat_input("Ask the agent …")

if user_msg:
    st.session_state.history.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    with st.chat_message("assistant"):
        with st.spinner("Thinking …"):
            try:
                answer = ask_agent(user_msg)
            except HttpResponseError as e:
                answer = f"⚠️ Azure error:\n```\n{e.message}\n```"
            except Exception as e:
                answer = f"⚠️ {e}"
        st.markdown(answer)

    st.session_state.history.append({"role": "assistant", "content": answer})
