import requests
import json

url = "https://google.serper.dev/search"

query: str = "Tell me the latest news ".strip()


payload = json.dumps({
  "q": query,
  "gl": "in"
})
headers = {
  'X-API-KEY': '084af1593c41bef4a088069160c5f287c2fca6b4',
  'Content-Type': 'application/json'
}
print("")
response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

