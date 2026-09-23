import requests
from config import settings

def rest(method, path, token, params=None, json_body=None, prefer=None):
    headers = {
        "apikey": settings.supabase_publishable_key,
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    response = requests.request(
        method,
        settings.supabase_url + "/rest/v1/" + path,
        headers=headers,
        params=params,
        json=json_body,
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Supabase REST {response.status_code}: {response.text[:300]}")
    if not response.text:
        return None
    return response.json()
