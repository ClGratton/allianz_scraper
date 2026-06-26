import os
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def load_session_from_disk():
    if os.path.exists("session_cache.pkl"):
        with open("session_cache.pkl", "rb") as f:
            data = pickle.load(f)
            if len(data) == 4:
                return data
            elif len(data) == 2:
                return data[0], data[1], None, None
    return None, None, None, None

session_key, s, username, policy_number = load_session_from_disk()
if not s:
    print("No session loaded from disk.")
    exit()

print(f"Loaded session for user: {username}, policy: {policy_number}")
dashboard_url = f"https://areapersonale.allianz.it/digitalme/private/detailDigMe.do?numeroPolizza={policy_number}&attivi=1"

# Fetch dashboard
try:
    res = s.get(dashboard_url, timeout=15)
    print("Dashboard status code:", res.status_code)
    with open("scratch/dashboard_page.html", "w", encoding="utf-8") as f:
        f.write(res.text)
    
    # Let's search for "Gratton" and "Elsa" in dashboard page
    soup = BeautifulSoup(res.text, "html.parser")
    print("\n--- Searching in Dashboard Page ---")
    for term in ["gratton", "claudio", "elsa"]:
        found = soup.find_all(lambda tag: tag.string and term in tag.string.lower())
        print(f"Term '{term}' found {len(found)} times:")
        for tag in found[:5]:
            print("  ", tag.name, tag.attrs, tag.string.strip())
            
    # Locate tabajax
    ajax_link = soup.find('a', {'data-toggle': 'tabajax'})
    if ajax_link:
        ajax_url = urljoin(dashboard_url, ajax_link['href'])
        print(f"\nAjax URL: {ajax_url}")
        ajax_res = s.get(ajax_url, timeout=15)
        print("Ajax details status code:", ajax_res.status_code)
        with open("scratch/ajax_details.html", "w", encoding="utf-8") as f:
            f.write(ajax_res.text)
            
        ajax_soup = BeautifulSoup(ajax_res.text, "html.parser")
        print("\n--- Searching in Ajax Details ---")
        for term in ["gratton", "claudio", "elsa"]:
            found = ajax_soup.find_all(lambda tag: tag.string and term in tag.string.lower())
            print(f"Term '{term}' found {len(found)} times:")
            for tag in found[:5]:
                print("  ", tag.name, tag.attrs, tag.string.strip())
    else:
        print("No tabajax link found on dashboard.")
except Exception as e:
    print("Error:", e)
