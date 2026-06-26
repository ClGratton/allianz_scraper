import requests
import re

url = "https://www.allianz.it/etc.clientlibs/onemarketing/platform/clientlibs/main.min.ACSHASH158ad1b9448e86de237a3c4edf3a9dc6.css"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}

try:
    print(f"Fetching {url}...")
    res = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        content = res.text
        print("Searching Allianz Neo font-face...")
        # Search for @font-face containing AllianzNeo
        matches = re.finditer(r"@font-face\s*\{[^}]*\}", content, re.IGNORECASE)
        for m in matches:
            block = m.group(0)
            if "AllianzNeo" in block or "Allianz Neo" in block:
                print(block)
                print("-" * 50)
    else:
        print("Failed to download.")
except Exception as e:
    print(f"Error: {e}")
