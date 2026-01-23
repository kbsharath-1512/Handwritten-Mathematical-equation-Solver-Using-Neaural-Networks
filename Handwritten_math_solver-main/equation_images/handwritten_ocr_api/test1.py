import requests
import json
API_KEY = "K83521503888957"
IMAGE_PATH = "ed.jpg"

url = "https://api.ocr.space/parse/image"

payload = {
    "apikey": API_KEY,
    "language": "eng",
    "ocrengine": 2,
    "scale": True
}

with open(IMAGE_PATH, "rb") as image:
    response = requests.post(
        url,
        files={"file": image},
        data=payload
    )

try:
    result = response.json()
except json.JSONDecodeError:
    print("❌ Response is not JSON:")
    print(response.text)
    exit()

if result.get("IsErroredOnProcessing"):
    print("❌ OCR Error:")
    print(result.get("ErrorMessage"))
else:
    parsed = result.get("ParsedResults")
    if not parsed:
        print("❌ No text detected")
    else:
        text = parsed[0].get("ParsedText", "")
        print("\n✅ Recognized Text:\n")
        print(text)
