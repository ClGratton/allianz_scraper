import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup
from app import extract_main_content

filepath = "comunicazioni_raw.html"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    content = extract_main_content(html, "/UnifondiRASNP/priv/")
    soup = BeautifulSoup(content, "html.parser")
    # Print the structure of the tags to find where empty space comes from
    for i, tag in enumerate(soup.find_all(True)):
        if tag.name in ["p", "br", "table", "tr", "td", "div"]:
            text = tag.get_text(strip=True)
            print(f"[{i}] <{tag.name}> class={tag.get('class')} text='{text[:60]}' attrs={ {k:v for k,v in tag.attrs.items() if k != 'class'} }")
else:
    print("File not found")
