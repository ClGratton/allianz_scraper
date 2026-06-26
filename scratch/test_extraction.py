from bs4 import BeautifulSoup

with open("anagrafe_raw.html", "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')
content_block = soup.find('td', width='85%')
if not content_block:
    content_block = soup.find('form')
if not content_block:
    content_block = soup.find('table', class_='defaultPage')
if not content_block:
    content_block = soup.find('body')

# Print out the main tag name and a snippet
print("Main tag found:", content_block.name if content_block else "None")
if content_block:
    import os
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/anagrafe_extracted.html", "w", encoding="utf-8") as f:
        f.write(str(content_block))
    print("Saved extracted HTML to scratch/anagrafe_extracted.html")
