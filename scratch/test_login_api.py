import json
import os
import sys

# Ensure current working directory is in sys.path
sys.path.insert(0, os.getcwd())

from app import app, load_session_from_disk

# Get user and policy from cached session
saved_data = load_session_from_disk()
saved_key, saved_s, username, policy_number, policy_info = saved_data

print(f"Loaded credentials from cache: Username={username}, Policy={policy_number}")
if not username or not policy_number:
    print("No cached session found on disk.")
    exit(1)

# Run a test request to api_login using Flask's test client
with app.test_client() as client:
    # 1. Test invalid parameters
    res = client.post("/api/login", json={})
    print("Empty post response:", res.status_code, res.get_json())
    
    # 2. Test valid cached login
    payload = {
        "username": username,
        "password": "somepassword",  # Password length must be >= 4
        "policy_number": policy_number
    }
    
    import time
    start = time.time()
    res = client.post("/api/login", json=payload)
    end = time.time()
    
    print(f"Login API response (took {end - start:.3f}s):", res.status_code, res.get_json())
    
    # Check Flask session variables
    with client.session_transaction() as sess:
        print("Session keys:", list(sess.keys()))
        if "user_data" in sess:
            print("Policy Info:", sess["user_data"]["policy"])
            print("Operations count:", len(sess["user_data"]["operations"]))
            print("Consultazioni count:", len(sess["user_data"]["consultazioni"]))
