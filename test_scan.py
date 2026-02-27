import requests

try:
    response = requests.post("http://localhost:8000/api/v1/products/scan/899999995555544444")
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print(e)
