import os
from bs4 import BeautifulSoup

filepath = "anagrafe_raw.html"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        # Find the text in the soup
        for text_el in soup.find_all(text=True):
            if "anagrafe tributaria" in text_el.lower():
                print(f"Parent: {text_el.strip()}")
                p = text_el.parent
                levels = []
                while p and p.name != "html":
                    levels.append(f"{p.name} class={p.get('class')} id={p.get('id')}")
                    p = p.parent
                print(" -> ".join(reversed(levels)))
                print("-" * 50)
else:
    print("File not found")
