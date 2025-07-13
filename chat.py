import os, requests, msal, json, pprint

endpoint      = os.environ["AI_ENDPOINT"].rstrip("/")
project       = os.environ["PROJECT_NAME"]
tenant_id     = os.environ["AZURE_TENANT_ID"]
client_id     = os.environ["AZURE_CLIENT_ID"]
client_secret = os.environ["AZURE_CLIENT_SECRET"]

token = msal.ConfidentialClientApplication(
    client_id, authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential=client_secret
).acquire_token_for_client(
    scopes=["https://cognitiveservices.azure.com/.default"]
)["access_token"]

hdr = {"Authorization": f"Bearer {token}"}

url = f"{endpoint}/api/projects/{project}/assistants?api-version=2024-05-01-preview"
r   = requests.get(url, headers=hdr)
print("Status:", r.status_code)
pprint.pp(r.json())
