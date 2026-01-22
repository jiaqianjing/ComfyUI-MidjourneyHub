import requests
import json

url = "https://yunwu.ai/v1/images/generations"

payload = json.dumps({
   "size": "1024x1536",
   "prompt": "a man walks",
   "model": "gpt-image-1.5",
   "n": 1
})
headers = {
   'Accept': 'application/json',
   'Authorization': 'Bearer ',
   'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)