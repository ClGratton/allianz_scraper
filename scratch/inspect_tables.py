import glob
from bs4 import BeautifulSoup

files = glob.glob("*_raw.html")
for f_path in files:
    print(f"\n=== File: {f_path} ===")
    with open(f_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    tables = soup.find_all("table")
    print(f"Total tables: {len(tables)}")
    for i, t in enumerate(tables):
        classes = t.get("class", [])
        width = t.get("width")
        headers = t.find_all(class_=lambda x: x and "headerPage" in x)
        inputs = t.find_all("input")
        rows = len(t.find_all("tr"))
        
        # Print info about tables inside the main width="85%" cell
        parent_85 = t.find_parent("td", width="85%")
        if parent_85 or t.find_parent("form"):
            snippet = t.get_text()[:60].replace("\n", " ").strip()
            print(f"  Table {i}: class={classes}, rows={rows}, headers={len(headers)}, inputs={len(inputs)}, snippet='{snippet}'")
