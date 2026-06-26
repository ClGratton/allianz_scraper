import os
from bs4 import BeautifulSoup

for filename in os.listdir("."):
    if filename.endswith(".html"):
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            a = soup.find('a', {'data-toggle': 'tabajax'})
            if a:
                print(f"Found in {filename}: {a}")
