import os
import sys
import requests
from bs4 import BeautifulSoup

# Constants for URLs
LOGIN_URL = "https://areapersonale.allianz.it/digitalme/public/login/login-filter.do"
OPERATIONS_URL = "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuHigh.do?method=operazioni"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
TICKET_IDENTIFIER = "actionAttestationSCAInit.do?ticket="
HTTP_OK = requests.codes.ok
EXIT_ERROR = 1

def run_scraper(username, password):
    
    print(f"[*] Starting session and configuring headers...")
    session = requests.Session()
    session.headers.update({
        "User" + chr(45) + "Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept" + chr(45) + "Language": "en" + chr(45) + "US,en;q=0.9"
    })

    print(f"[*] Establishing session by fetching login page: {LOGIN_URL}...")
    initial_response = session.get(LOGIN_URL)
    print(f"[+] Initial GET status: {initial_response.status_code}")

    print(f"[*] Sending POST login request to {LOGIN_URL} for user: {username}...")
    login_payload = {
        "j_username": username,
        "j_password": password,
        "login": "Accedi"
    }

    login_response = session.post(LOGIN_URL, data=login_payload, allow_redirects=True)
    print(f"[+] Login HTTP Status: {login_response.status_code}")
    if login_response.status_code != HTTP_OK:
        print("[-] Login failed. Exiting.")
        sys.exit(EXIT_ERROR)

    print("[*] Attempting policy auto-discovery...")
    discovery_url = "https://areapersonale.allianz.it/digitalme/private/dashboard.do"
    print(f"[*] Fetching discovery page: {discovery_url}...")
    discovery_response = session.get(discovery_url)
    
    from urllib.parse import urljoin
    soup = BeautifulSoup(discovery_response.text, "html.parser")
    policy_link = soup.find("a", href=lambda href: href and "detailDigMe.do?numeroPolizza=" in href)
    
    if not policy_link:
        fallback_url = "https://areapersonale.allianz.it/digitalme/private/home.do"
        print(f"[*] Policy link not found in dashboard. Trying fallback page: {fallback_url}...")
        discovery_response = session.get(fallback_url)
        soup = BeautifulSoup(discovery_response.text, "html.parser")
        policy_link = soup.find("a", href=lambda href: href and "detailDigMe.do?numeroPolizza=" in href)
        
    if not policy_link:
        print("[-] Policy auto-discovery failed. Could not locate policy link in dashboard or home page.")
        sys.exit(EXIT_ERROR)
        
    dashboard_url = urljoin(discovery_url, policy_link["href"])
    print(f"[+] Auto-discovered dashboard URL: {dashboard_url}")

    print(f"[*] Requesting dashboard URL: {dashboard_url}...")
    dashboard_response = session.get(dashboard_url)
    print(f"[+] Dashboard HTTP Status: {dashboard_response.status_code}")
    
    # Save dashboard response for debugging if needed
    with open("dashboard_response.html", "w", encoding="utf-8") as f:
        f.write(dashboard_response.text)

    print("[*] Parsing dashboard HTML for AJAX tab URL...")
    soup = BeautifulSoup(dashboard_response.text, 'html.parser')
    ajax_link_element = soup.find('a', {'data-toggle': 'tabajax'})
    if not ajax_link_element:
        print("[-] AJAX tab link not found in dashboard HTML. Saved dashboard_response.html for inspection.")
        sys.exit(EXIT_ERROR)

    from urllib.parse import urljoin
    ajax_url = urljoin(dashboard_url, ajax_link_element['href'])
    print(f"[+] Found AJAX tab URL: {ajax_url}")

    print(f"[*] Fetching AJAX tab content...")
    ajax_response = session.get(ajax_url)
    print(f"[+] AJAX tab HTTP Status: {ajax_response.status_code}")

    with open("ajax_tab_response.html", "w", encoding="utf-8") as f:
        f.write(ajax_response.text)

    print("[*] Parsing AJAX tab HTML for SCA/ticket URL...")
    soup = BeautifulSoup(ajax_response.text, 'html.parser')
    ticket_link_element = soup.find('a', href=lambda href: href and TICKET_IDENTIFIER in href)

    if not ticket_link_element:
        print("[-] Ticket link not found in AJAX tab HTML. Saved ajax_tab_response.html for inspection.")
        sys.exit(EXIT_ERROR)

    ticket_url = ticket_link_element['href']
    print(f"[+] Found ticket URL: {ticket_url}")

    print("[*] Fetching ticket URL to consume ticket and transition domain...")
    ticket_response = session.get(ticket_url, allow_redirects=True)
    print(f"[+] Ticket transition HTTP Status: {ticket_response.status_code}")

    print(f"[*] Requesting operations page: {OPERATIONS_URL}...")
    operations_response = session.get(OPERATIONS_URL)
    print(f"[+] Operations page HTTP Status: {operations_response.status_code}")

    # Output raw response HTML to a file and print preview
    with open("operations_response.html", "w", encoding="utf-8") as f:
        f.write(operations_response.text)
    
    print("\n--- OPERATIONS PAGE PREVIEW (First 500 characters) ---")
    print(operations_response.text[:500])
    print("------------------------------------------------------")
    print("[+] Full operations page saved to operations_response.html")

if __name__ == "__main__":
    # Check if a local .env file exists and parse it manually
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        print("[*] Found local .env file, loading credentials...")
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

    # Get credentials from environment or command line or input prompt
    username = os.environ.get("ALLIANZ_USERNAME")
    password = os.environ.get("ALLIANZ_PASSWORD")

    if len(sys.argv) > 1:
        username = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]

    if not username:
        username = input("Enter Allianz Username (email): ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Enter Allianz Password: ")

    run_scraper(username, password)
