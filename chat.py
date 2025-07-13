import os, streamlit as st, requests, json
from azure.identity import ClientSecretCredential

# --- Config from environment ---
ENDPOINT  = os.environ["AI_ENDPOINT"].rstrip("/")
AGENT_ID  = os.environ["AGENT_ID"]
TENANT    = os.environ["AZURE_TENANT_ID"]
CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
SECRET    = os.environ["AZURE_CLIENT_SECRET"]

# --- Get an AAD token to call Foundry (scopes = https://cognitiveservices.azure.com/.default) ---
cred   = ClientSecretCredential(TENANT, CLIENT_ID, SECRET)
token  = cred.get_token("https://cognitiveservices.azure.com/.default").token
HEAD   = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# --- Streamlit UI ---
st.title("SME Underwriting AI Agent")
prompt = st.chat_input("Ask the agent…")

if prompt:
    # 1) create a thread
    thread_r = requests.post(
        f"{ENDPOINT}/api/projects/sara-openai-underwritin-project/threads",
        headers=HEAD, json={})
    thread_id = thread_r.json()["id"]

    # 2) post the user message
    requests.post(
        f"{ENDPOINT}/api/projects/sara-openai-underwritin-project/threads/{thread_id}/messages",
        headers=HEAD,
        json={"role": "user", "content": prompt})

    # 3) run the agent on that thread
    run_r = requests.post(
        f"{ENDPOINT}/api/projects/sara-openai-underwritin-project/threads/{thread_id}/runs",
        headers=HEAD,
        json={"agent_id": AGENT_ID})
    run_id = run_r.json()["id"]

    # 4) poll until status == “completed”
    while True:
        run = requests.get(
            f"{ENDPOINT}/api/projects/sara-openai-underwritin-project/threads/{thread_id}/runs/{run_id}",
            headers=HEAD).json()
        if run["status"] in ("completed", "failed"):
            break

    # 5) fetch assistant reply
    msgs = requests.get(
        f"{ENDPOINT}/api/projects/sara-openai-underwritin-project/threads/{thread_id}/messages?order=asc",
        headers=HEAD).json()

    assistant_text = next(
        (m["text_messages"][-1]["text"]["value"]
         for m in msgs if m["role"] == "assistant" and m["text_messages"]),
        "**No answer**")
    st.markdown(assistant_text)
