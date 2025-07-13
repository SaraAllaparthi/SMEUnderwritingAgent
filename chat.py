# chat.py
import os
from azure.identity import ClientSecretCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder

cred = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"],
)
endpoint = os.environ["AI_ENDPOINT"].rstrip("/")
project  = "sara-openai-underwritin-project"
agent_id = os.environ["AGENT_ID"]

proj  = AIProjectClient(credential=cred, endpoint=f"{endpoint}/api/projects/{project}")
agent = proj.agents.get_agent(agent_id)

def ask_agent(prompt: str) -> str:
    th = proj.agents.threads.create()
    proj.agents.messages.create(thread_id=th.id, role="user", content=prompt)
    run = proj.agents.runs.create_and_process(thread_id=th.id, agent_id=agent.id)
    if run.status == "failed":
        raise RuntimeError(run.last_error["message"])
    msgs = proj.agents.messages.list(thread_id=th.id, order=ListSortOrder.ASCENDING)
    return next(m.text_messages[-1].text.value for m in msgs if m.role == "assistant")
