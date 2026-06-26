import re

with open("allianz_it.html", "r", encoding="utf-8") as f:
    content = f.read()

print("Searching Allianz Neo font references...")
matches = re.findall(r"@font-face\s*\{[^}]*\}", content, re.IGNORECASE)
for m in matches:
    if "Allianz" in m:
        print(m)
        print("-" * 40)
