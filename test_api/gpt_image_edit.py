import requests

url = "https://yunwu.ai/v1/images/edits"

payload={}
files=[
   ('image',('C:\Users\Administrator\Desktop\例子.png',open('C:\\Users\\Administrator\\Desktop\\例子.png','rb'),'image/png')),
   ('image',('C:\Users\Administrator\Desktop\场景2.png',open('C:\\Users\\Administrator\\Desktop\\场景2.png','rb'),'image/png'))
]
headers = {
   'Accept': 'application/json',
   'Authorization': 'Bearer '
}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)