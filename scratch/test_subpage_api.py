import os
import sys

# Ensure current working directory is in sys.path
sys.path.insert(0, os.getcwd())

from app import app, load_session_from_disk

# Get user and policy from cached session
saved_data = load_session_from_disk()
saved_key, saved_s, username, policy_number, policy_info = saved_data

if not username or not policy_number:
    print("No cached session found on disk.")
    exit(1)

with app.test_client() as client:
    # Authenticate the test client session
    with client.session_transaction() as sess:
        sess["session_key"] = saved_key
        sess["user_data"] = {
            "policy": policy_info,
            "operations": [],
            "consultazioni": [
                {"title": "Anagrafe tributaria", "action_id": "anagrafe_cons"}
            ]
        }
        
    print("Simulating GET /operation/anagrafe_cons...")
    try:
        # Mock fetch_page_with_menu or just run it.
        # Since saved_s is an active authorized requests session from the cache,
        # it should run fetch_page_with_menu, hit previdenzacomplementare.allianz.it, and return 200.
        res = client.get("/operation/anagrafe_cons")
        print("Response status code:", res.status_code)
        
        # Verify if it contains the word 'anagrafe' or similar html content
        text = res.get_data(as_text=True)
        print("Is page rendered without error?", "Error:" not in text and "UnboundLocalError" not in text)
        if "Error:" in text:
            print("Page content snippet (with error):", text[:500])
        else:
            print("Page content snippet:", text[:300].strip().replace('\n', ' '))
            
    except Exception as e:
        print("Test failed with exception:", e)
