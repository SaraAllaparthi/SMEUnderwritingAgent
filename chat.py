import streamlit as st
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

endpoint = ("https://sara-openai-underwritin-resource.services.ai.azure.com"
            "/api/projects/sara-openai-underwritin-project")
agent_id = "asst_0N9JnFU6reHLbJqS4wMbysEu"

@st.cache_resource
def get_client():
    cred = DefaultAzureCredential()
    return AIProjectClient(credential=cred, endpoint=endpoint)

def chat(user_text):
    client = get_client()
    thread = client.agents.threads.create()
    client.agents.messages.create(thread_id=thread.id,
                                  role="user", content=user_text)
    run = client.agents.runs.create_and_process(thread_id=thread.id,
                                                agent_id=agent_id)

    if run.status == "failed":
        return f"⚠️ Agent error: {run.last_error}"
    msgs = client.agents.messages.list(thread_id=thread.id,
                                       order=ListSortOrder.ASCENDING)
    return "\n".join(
        f"**{m.role}**: {m.text_messages[-1].text.value}"
        for m in msgs if m.text_messages
    )

st.title("SME Underwriting AI Agent")
prompt = st.chat_input("Ask me anything...")
if prompt:
    with st.spinner("Thinking…"):
        st.write(chat(prompt))
