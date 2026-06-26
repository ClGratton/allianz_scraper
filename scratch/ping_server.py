import requests
try:
    res = requests.get("http://127.0.0.1:5000/", timeout=5)
    print(f"Status: {res.status_code}")
except Exception as e:
    print(f"Error pinging server: {e}")
