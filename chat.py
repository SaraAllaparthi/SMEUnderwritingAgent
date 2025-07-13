import os, requests
from azure.identity import ClientSecretCredential

# Grab secrets from env-vars (set this later in Streamlit Cloud)
ENDPOINT  = os.environ["AI_ENDPOINT"].rstrip("/")
AGENT_ID  = os.environ["AGENT_ID"]
TENANT    = os.environ["AZURE_TENANT_ID"]
CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
SECRET    = os.environ["AZURE_CLIENT_SECRET"]

# Get an Azure access-token once at start-up
cred   = ClientSecretCredential(TENANT, CLIENT_ID, SECRET)
token  = cred.get_token("https://ai.azure.com/.default").token
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def ask_agent(question: str) -> str:
    """Send one question and return the assistant’s first reply text."""
    # 1) new thread
    th = requests.post(f"{ENDPOINT}/threads", headers=HEADERS).json()
    thread_id = th["id"]

    # 2) user message
    requests.post(
        f"{ENDPOINT}/threads/{thread_id}/messages",
        headers=HEADERS,
        json={"role": "user", "content": question},
    )

    # 3) run the agent (synchronous “create_and_process”)
    run = requests.post(
        f"{ENDPOINT}/threads/{thread_id}/runs:createAndProcess",
        headers=HEADERS,
        json={"agent_id": AGENT_ID},
    ).json()

    if run["status"] == "failed":
        raise RuntimeError(run.get("last_error", "unknown error"))

    # 4) list messages in chronological order
    msgs = requests.get(
        f"{ENDPOINT}/threads/{thread_id}/messages?order=asc", headers=HEADERS
    ).json()["data"]

    # assistant’s last message = answer
    answer_blocks = [
        blk["text"] for m in msgs if m["role"] == "assistant" for blk in m["content"]
    ]
    return "\n\n".join(answer_blocks) if answer_blocks else "(no answer)"
