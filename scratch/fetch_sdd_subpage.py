import os
import sys

# Ensure current working directory is in sys.path
sys.path.insert(0, os.getcwd())

from app import load_session_from_disk, extract_main_content

saved_data = load_session_from_disk()
print("Saved data type:", type(saved_data))
print("Saved data length:", len(saved_data))
print("Saved data elements:", [type(x) for x in saved_data])

saved_key, s, username, policy_number, policy_info = saved_data

if not s:
    print("No active session in cache.")
    exit(1)

sub_url = "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=isInserimentoSDD"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

print("Fetching SDD sub-page...")
res_sub = s.get(sub_url, headers=headers, timeout=15)
print("Status code:", res_sub.status_code)

sub_content = extract_main_content(res_sub.text, "/UnifondiRASNP/priv/")
print("Extracted sub_content length:", len(sub_content))

from bs4 import BeautifulSoup
soup_check = BeautifulSoup(sub_content, 'html.parser')
visible_text = soup_check.get_text(strip=True)
visible_inputs = soup_check.find_all(lambda tag: tag.name == 'input' and tag.get('type') != 'hidden')
other_visible = soup_check.find_all(['button', 'select', 'textarea', 'img', 'a'])

print("\n--- Detection Variables ---")
print("visible_text:", repr(visible_text))
print("visible_inputs count:", len(visible_inputs))
print("other_visible count:", len(other_visible))

with open("scratch/sdd_sub_content.html", "w", encoding="utf-8") as f:
    f.write(sub_content)
print("\nSaved sub_content to scratch/sdd_sub_content.html")
