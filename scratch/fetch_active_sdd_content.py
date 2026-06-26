import os
import sys
from bs4 import BeautifulSoup

# Ensure current working directory is in sys.path
sys.path.insert(0, os.getcwd())

from app import load_session_from_disk, extract_main_content

saved_data = load_session_from_disk()
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

res_sub = s.get(sub_url, headers=headers, timeout=15)
sub_content = extract_main_content(res_sub.text, "/UnifondiRASNP/priv/")

soup_check = BeautifulSoup(sub_content, 'html.parser')
print("--- Text ---")
print(repr(soup_check.get_text(strip=True)))

print("--- Inputs ---")
for x in soup_check.find_all('input'):
    print("  Input:", x.name, x.get('type'), x.get('name'), x.get('value'))

print("--- Buttons ---")
for x in soup_check.find_all('button'):
    print("  Button:", x)

print("--- Selects ---")
for x in soup_check.find_all('select'):
    print("  Select:", x.get('name'))

print("--- Anchors ---")
for x in soup_check.find_all('a'):
    print("  Anchor:", x.get('href'), x.get_text(strip=True))

print("--- Images ---")
for x in soup_check.find_all('img'):
    print("  Image:", x.get('src'))

with open("scratch/sdd_active_sub_content.html", "w", encoding="utf-8") as f:
    f.write(sub_content)
