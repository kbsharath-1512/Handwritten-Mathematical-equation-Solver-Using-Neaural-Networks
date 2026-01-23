import requests

url = "http://127.0.0.1:5000/solve"

with open("lineareqy4.png", "rb") as f:
    response = requests.post(url, files={"image": f})

print(response.json())
