import json
import requests

def _fetch_data(query:str):
    url = "https://google.serper.dev/search"
    
    payload = json.dumps({
        "q": query,
        "gl": "in"
    })
    
    headers = {
        'X-API-KEY': '975f36593233767f896dd6fb7ebcfcdbf62241dc',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching data:", response.status_code)
        return None

def _extract_snippets(data):
    if not data or "organic" not in data:
        return {"snippets": []}
    
    snippets = [entry["snippet"] for entry in data["organic"] if "snippet" in entry]
    return snippets

def web_search():
    data = _fetch_data("Which movies are coming soon?")
    formatted_snippets = _extract_snippets(data)
    return formatted_snippets
