import requests; print("Testing server..."); r = requests.get("http://localhost:8000/health"); print(f"Status: {r.status_code}")
