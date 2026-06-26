from bs4 import BeautifulSoup

try:
    with open("dashboard_response.html", "r", encoding="utf-8") as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    ajax_link = soup.find('a', {'data-toggle': 'tabajax'})
    if ajax_link:
        print("Found ajax tab href:", ajax_link.get("href"))
    else:
        print("ajax tab link not found in dashboard_response.html")
except Exception as e:
    print(f"Error: {e}")
