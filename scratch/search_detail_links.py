import os
from bs4 import BeautifulSoup

for filename in os.listdir("."):
    if filename.endswith(".html"):
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            for a in soup.find_all('a', href=True):
                if "detailDigMe" in a['href']:
                    print(f"Link in {filename}: {a}")
