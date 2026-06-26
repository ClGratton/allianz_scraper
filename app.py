import os
import sys
import uuid
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from urllib.parse import urljoin

class SessionExpiredException(Exception):
    pass

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.errorhandler(SessionExpiredException)
def handle_session_expired(e):
    print("[*] SessionExpiredException caught. Clearing session and cache, redirecting to login...")
    session.clear()
    try:
        if os.path.exists("session_cache.pkl"):
            os.remove("session_cache.pkl")
    except Exception as ex:
        print(f"Error removing session cache: {ex}")
    return redirect(url_for("index"))

# Global Session Registry for Scraper
active_sessions = {}

import pickle

def save_session_to_disk(session_key, s, username, policy_number, policy_info):
    try:
        with open("session_cache.pkl", "wb") as f:
            pickle.dump((session_key, s, username, policy_number, policy_info), f)
    except Exception as e:
        print(f"Error pickling session: {e}")

def load_session_from_disk():
    try:
        if os.path.exists("session_cache.pkl"):
            with open("session_cache.pkl", "rb") as f:
                data = pickle.load(f)
                if isinstance(data, tuple):
                    if len(data) == 5:
                        return data
                    elif len(data) == 4:
                        return data[0], data[1], data[2], data[3], None
                    elif len(data) == 2:
                        return data[0], data[1], None, None, None
    except Exception as e:
        print(f"Error loading pickled session: {e}")
    return None, None, None, None, None

def is_session_active(s):
    try:
        # Quick GET check with a short timeout to see if session is valid
        res = s.get("https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuHigh.do?method=operazioni", timeout=3)
        if res.status_code == 200:
            text = res.text
            if "j_username" in text or "Sei gi&agrave; registrato?" in text:
                return False
            # Check for expiration messages
            if any(marker in text for marker in ["spiacenti", "passato troppo tempo", "disconnesso"]):
                return False
            return True
    except Exception:
        pass
    return False

# Scraper Constants
LOGIN_URL = "https://areapersonale.allianz.it/digitalme/public/login/login-filter.do"
OPERATIONS_URL = "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuHigh.do?method=operazioni"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
TICKET_IDENTIFIER = "actionAttestationSCAInit.do?ticket="
HTTP_OK = requests.codes.ok

# Map of action_id to their URL on the Allianz server (both operations and consultazioni)
ACTIONS = {
    # Operazioni
    "anagrafe": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=isAnagraficaTributariaHomeOperazioni",
    "beneficiari": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=beneficiari",
    "cambio_azienda": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=cambioAziendaIs",
    "comunicazioni": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=certificazioniHome",
    "contributi": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=contributiNonDedottiOp",
    "garanzie": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=garanzieAccessorie",
    "liquidazioni": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=richiestaPrest",
    "sdd": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=variazioneSDD",
    "switch": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=switchHomelifeCycle",
    "congruita": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=questionarioAutovalutazione",
    
    # Consultazioni
    "anagrafe_cons": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=isAnagraficaTributariaHome",
    "cessione_quinto": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=cessioneQuinto",
    "documentazione": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=documentazione",
    "contributi_cons": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=contributiNonDedotti",
    "dettaglio_contributi": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=dettaglioContributi",
    "estratto_conto": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=estrattoConto",
    "garanzie_cons": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=isGaranzieAccessorieConsultazioni",
    "liquidazioni_cons": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=liquidazioni",
    "sdd_cons": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=isConsultSDD",
    "trasferimenti": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=trasferimentiAltriFondi",
    "scelta_investimento": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=switchStorico",
    "rendita": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=rendita",
    "altre_posizioni": "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuLeft.do?method=isAltrePosizioniStessoProdotto"
}

CONSULTAZIONI_ACTION_IDS = {
    "anagrafe_cons", "cessione_quinto", "documentazione", "contributi_cons",
    "dettaglio_contributi", "estratto_conto", "garanzie_cons", "liquidazioni_cons",
    "sdd_cons", "trasferimenti", "scelta_investimento", "rendita", "altre_posizioni"
}

def run_allianz_scrape(username, password):
    try:
        # 1. Start Session
        s = requests.Session()
        s.headers.update({
            "User" + chr(45) + "Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept" + chr(45) + "Language": "en" + chr(45) + "US,en;q=0.9"
        })

        # 2. Authenticate (try direct POST first, fallback to GET + POST if needed)
        login_payload = {
            "j_username": username,
            "j_password": password,
            "login": "Accedi"
        }
        try:
            login_res = s.post(LOGIN_URL, data=login_payload, allow_redirects=True, timeout=15)
            if login_res.status_code != HTTP_OK or "j_username" in login_res.text:
                # Direct POST did not work or returned the form; try standard GET then POST sequence
                s.get(LOGIN_URL, timeout=15)
                login_res = s.post(LOGIN_URL, data=login_payload, allow_redirects=True, timeout=15)
        except Exception:
            # On network/connection timeout, fall back to sequential GET then POST
            s.get(LOGIN_URL, timeout=15)
            login_res = s.post(LOGIN_URL, data=login_payload, allow_redirects=True, timeout=15)

        if login_res.status_code != HTTP_OK:
            return {"success": False, "error": f"Login returned status code {login_res.status_code}"}, None

        # Verify login was successful (not redirected back to login page)
        if "Sei gi" + chr(38) + "agrave" + chr(59) + " registrato?" in login_res.text or "j_username" in login_res.text:
            return {"success": False, "error": "Invalid username or password."}, None

        # Policy Auto_Discovery Phase
        print("[*] Attempting policy auto" + chr(45) + "discovery...")
        discovery_url = "https://areapersonale.allianz.it/digitalme/private/dashboard.do"
        discovery_response = s.get(discovery_url, timeout=15)
        
        soup = BeautifulSoup(discovery_response.text, "html.parser")
        policy_link = soup.find("a", href=lambda href: href and "detailDigMe.do?numeroPolizza=" in href)
        
        if not policy_link:
            fallback_url = "https://areapersonale.allianz.it/digitalme/private/home.do"
            print(f"[*] Policy link not found in dashboard. Trying fallback page: {fallback_url}...")
            discovery_response = s.get(fallback_url, timeout=15)
            soup = BeautifulSoup(discovery_response.text, "html.parser")
            policy_link = soup.find("a", href=lambda href: href and "detailDigMe.do?numeroPolizza=" in href)
            
        if not policy_link:
            return {"success": False, "error": "Could not auto" + chr(45) + "discover policy number from Allianz portal."}, None
            
        dashboard_url = urljoin(discovery_url, policy_link["href"])
        print(f"[+] Auto" + chr(45) + "discovered dashboard URL: {dashboard_url}")
        
        # Extract policy number from link
        from urllib.parse import urlparse, parse_qs
        parsed_dash = urlparse(dashboard_url)
        query_params = parse_qs(parsed_dash.query)
        policy_numbers = query_params.get("numeroPolizza")
        if not policy_numbers:
            return {"success": False, "error": "Could not parse policy number from auto" + chr(45) + "discovered link."}, None
        policy_number = policy_numbers[0]
        print(f"[+] Extracted policy number: {policy_number}")

        # 4. Get Dashboard
        dash_res = s.get(dashboard_url, timeout=15)
        if dash_res.status_code != HTTP_OK:
            return {"success": False, "error": f"Failed to retrieve dashboard. Status: {dash_res.status_code}"}, None

        # 5. Locate AJAX Tab URL
        soup = BeautifulSoup(dash_res.text, 'html.parser')
        ajax_link = soup.find('a', {'data-toggle': 'tabajax'})
        if not ajax_link:
            return {"success": False, "error": "Could not locate dynamic policy detail link on Allianz portal."}, None

        ajax_url = urljoin(dashboard_url, ajax_link['href'])

        # 6. Fetch Dynamic Details
        ajax_res = s.get(ajax_url, timeout=15)
        if ajax_res.status_code != HTTP_OK:
            return {"success": False, "error": "Failed to retrieve dynamic details tab."}, None

        # Parse basic policy details dynamically from dashboard HTML
        policy_info = {
            "policy_number": policy_number,
            "policy_name": "Insieme",
            "status": "Attiva",
            "full_name": "Nome Assicurato",
            "agency": "Agenzia Allianz"
        }

        # Attempt to read dynamic values
        dash_soup = BeautifulSoup(dash_res.text, 'html.parser')
        
        # 1. Parse Name dynamically
        nome_input = dash_soup.find('input', id='inputNome')
        cognome_input = dash_soup.find('input', id='inputCognome')
        if nome_input and cognome_input:
            first_name = nome_input.get('value', '').strip().title()
            last_name = cognome_input.get('value', '').strip().title()
            policy_info["full_name"] = f"{first_name} {last_name}"

        # 2. Parse Agency from digitalData
        import re
        agency_match = re.search(r"'agenzia_riferimento'\s*:\s*'([^']+)'", dash_res.text)
        if agency_match:
            agency_code = agency_match.group(1)
            if 'elsa' in agency_code.lower():
                policy_info["agency"] = "Elsa S.r.l."
            else:
                policy_info["agency"] = agency_code.replace('_', ' ').title()

        # 3. Parse Status
        status_box = dash_soup.find(class_='side-stato')
        if status_box:
            status_text = status_box.get_text(separator=" ", strip=True)
            if "attiva" in status_text.lower():
                policy_info["status"] = "Attiva"
            else:
                policy_info["status"] = status_text

        # 4. Parse Policy Name
        title_box = dash_soup.find(class_='side-title')
        if title_box:
            span_el = title_box.find('span')
            if span_el:
                policy_info["policy_name"] = span_el.get_text(strip=True).title()
            else:
                policy_info["policy_name"] = title_box.get_text(strip=True).title()

        # Parse ticket
        ajax_soup = BeautifulSoup(ajax_res.text, 'html.parser')
        ticket_el = ajax_soup.find('a', href=lambda href: href and TICKET_IDENTIFIER in href)
        if not ticket_el:
            return {"success": False, "error": "SCA/Ticket URL not found in policy details."}, None

        ticket_url = ticket_el['href']

        # 7. Consume ticket is skipped here (deferred and consumed on-demand during the first proxy request)

        # 8. Skip Operations Page pre-fetch during login (lazy-loaded on-demand during category navigation)
        pass

        # 9. Define static operations (avoiding a slow operations menu HTML parse during login)
        operations = [
            {"title": "Anagrafe tributaria", "description": "Gestisci l'anagrafe tributaria per le comunicazioni fiscali.", "icon": "👤", "action_id": "anagrafe"},
            {"title": "Beneficiari", "description": "Visualizza o modifica i beneficiari designati della polizza.", "icon": "👥", "action_id": "beneficiari"},
            {"title": "Cambio Azienda", "description": "Aggiorna l'azienda collegata alla tua posizione previdenziale.", "icon": "🏢", "action_id": "cambio_azienda"},
            {"title": "Comunicazioni", "description": "Archivio delle comunicazioni periodiche e delle certificazioni fiscali.", "icon": "✉️", "action_id": "comunicazioni"},
            {"title": "Contributi non dedotti", "description": "Dichiara o consulta i contributi non dedotti fiscalmente.", "icon": "💰", "action_id": "contributi"},
            {"title": "Garanzie accessorie", "description": "Visualizza lo stato delle garanzie accessorie attive.", "icon": "🛡️", "action_id": "garanzie"},
            {"title": "Richiesta Liquidazioni", "description": "Avvia la richiesta di liquidazione totale o parziale.", "icon": "💸", "action_id": "liquidazioni"},
            {"title": "SDD", "description": "Attiva o modifica il mandato di addebito diretto SEPA (SDD).", "icon": "💳", "action_id": "sdd"},
            {"title": "Switch", "description": "Rialloca la tua posizione previdenziale tra i diversi comparti.", "icon": "🔄", "action_id": "switch"},
            {"title": "Congruità della scelta previdenziale", "description": "Questionario di autovalutazione sulla scelta previdenziale.", "icon": "📊", "action_id": "congruita"}
        ]

        consultazioni = [
            {"title": "Anagrafe tributaria", "description": "Visualizza i dati dell'anagrafe tributaria.", "icon": "👤", "action_id": "anagrafe_cons"},
            {"title": "Cessione del Quinto", "description": "Visualizza eventuali vincoli o cessioni di quote.", "icon": "📄", "action_id": "cessione_quinto"},
            {"title": "Documentazione", "description": "Consulta la documentazione informativa e contrattuale.", "icon": "📁", "action_id": "documentazione"},
            {"title": "Contributi non dedotti", "description": "Visualizza lo storico dei contributi non dedotti fiscalmente.", "icon": "💰", "action_id": "contributi_cons"},
            {"title": "Dettaglio Contributi", "description": "Visualizza i dettagli di tutti i contributi versati.", "icon": "📊", "action_id": "dettaglio_contributi"},
            {"title": "Estratto conto", "description": "Scarica il rendiconto annuale ed estratto conto.", "icon": "💳", "action_id": "estratto_conto"},
            {"title": "Garanzie accessorie", "description": "Verifica lo stato e le coperture delle garanzie accessorie.", "icon": "🛡️", "action_id": "garanzie_cons"},
            {"title": "Liquidazioni", "description": "Monitora lo stato di avanzamento delle liquidazioni.", "icon": "💸", "action_id": "liquidazioni_cons"},
            {"title": "SDD", "description": "Consulta lo stato del tuo mandato di addebito diretto SEPA.", "icon": "🏦", "action_id": "sdd_cons"},
            {"title": "Trasferimenti da altri fondi", "description": "Consulta lo storico dei trasferimenti in entrata.", "icon": "🔄", "action_id": "trasferimenti"},
            {"title": "Scelta investimento dei contributi", "description": "Visualizza la ripartizione storica dei tuoi comparti.", "icon": "📈", "action_id": "scelta_investimento"},
            {"title": "Rendita", "description": "Calcola o visualizza i dettagli della rendita maturata.", "icon": "🪙", "action_id": "rendita"},
            {"title": "Altre posizioni nello stesso prodotto", "description": "Accedi ad altre posizioni attive collegate.", "icon": "💼", "action_id": "altre_posizioni"}
        ]

        return {
            "success": True,
            "policy": policy_info,
            "operations": operations,
            "consultazioni": consultazioni,
            "ticket_url": ticket_url
        }, s

    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred during scraping: {str(e)}"}, None


@app.route("/")
def index():
    if "user_data" in session:
        get_active_session()
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_data" not in session:
        return redirect(url_for("index"))
    get_active_session()
    return render_template("dashboard.html", data=session["user_data"])


@app.route("/api/login", methods=["POST"])
def api_login():
    req_data = request.get_json()
    if not req_data:
        return jsonify({"success": False, "error": "Invalid request payload."}), 400

    username = req_data.get("username", "").strip()
    password = req_data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "error": "All fields are required."}), 400

    # Backend email checks
    import re
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", username):
        return jsonify({"success": False, "error": "Inserisci un indirizzo email valido."}), 400

    if len(password) < 4:
        return jsonify({"success": False, "error": "La password deve essere di almeno 4 caratteri."}), 400

    # Check if we can reuse the cached session
    saved_data = load_session_from_disk()
    saved_key, saved_s, cached_user, cached_policy, cached_policy_info = saved_data
    if saved_s and cached_user == username:
        print("[*] Found cached session matching credentials. Checking if active...")
        if is_session_active(saved_s):
            print("[*] Cached session is active! Bypassing full scrape for faster login.")
            active_sessions[saved_key] = saved_s
            session["session_key"] = saved_key
            
            # Recreate user_data in session
            operations = [
                {"title": "Anagrafe tributaria", "description": "Gestisci l'anagrafe tributaria per le comunicazioni fiscali.", "icon": "👤", "action_id": "anagrafe"},
                {"title": "Beneficiari", "description": "Visualizza o modifica i beneficiari designati della polizza.", "icon": "👥", "action_id": "beneficiari"},
                {"title": "Cambio Azienda", "description": "Aggiorna l'azienda collegata alla tua posizione previdenziale.", "icon": "🏢", "action_id": "cambio_azienda"},
                {"title": "Comunicazioni", "description": "Archivio delle comunicazioni periodiche e delle certificazioni fiscali.", "icon": "✉️", "action_id": "comunicazioni"},
                {"title": "Contributi non dedotti", "description": "Dichiara o consulta i contributi non dedotti fiscalmente.", "icon": "💰", "action_id": "contributi"},
                {"title": "Garanzie accessorie", "description": "Visualizza lo stato delle garanzie accessorie attive.", "icon": "🛡️", "action_id": "garanzie"},
                {"title": "Richiesta Liquidazioni", "description": "Avvia la richiesta di liquidazione totale o parziale.", "icon": "💸", "action_id": "liquidazioni"},
                {"title": "SDD", "description": "Attiva o modifica il mandato di addebito diretto SEPA (SDD).", "icon": "💳", "action_id": "sdd"},
                {"title": "Switch", "description": "Rialloca la tua posizione previdenziale tra i diversi comparti.", "icon": "🔄", "action_id": "switch"},
                {"title": "Congruità della scelta previdenziale", "description": "Questionario di autovalutazione sulla scelta previdenziale.", "icon": "📊", "action_id": "congruita"}
            ]
            consultazioni = [
                {"title": "Anagrafe tributaria", "description": "Visualizza i dati dell'anagrafe tributaria.", "icon": "👤", "action_id": "anagrafe_cons"},
                {"title": "Cessione del Quinto", "description": "Visualizza eventuali vincoli o cessioni di quote.", "icon": "📄", "action_id": "cessione_quinto"},
                {"title": "Documentazione", "description": "Consulta la documentazione informativa e contrattuale.", "icon": "📁", "action_id": "documentazione"},
                {"title": "Contributi non dedotti", "description": "Visualizza lo storico dei contributi non dedotti fiscalmente.", "icon": "💰", "action_id": "contributi_cons"},
                {"title": "Dettaglio Contributi", "description": "Visualizza i dettagli di tutti i contributi versati.", "icon": "📊", "action_id": "dettaglio_contributi"},
                {"title": "Estratto conto", "description": "Scarica il rendiconto annuale ed estratto conto.", "icon": "💳", "action_id": "estratto_conto"},
                {"title": "Garanzie accessorie", "description": "Verifica lo stato e le coperture delle garanzie accessorie.", "icon": "🛡️", "action_id": "garanzie_cons"},
                {"title": "Liquidazioni", "description": "Monitora lo stato di avanzamento delle liquidazioni.", "icon": "💸", "action_id": "liquidazioni_cons"},
                {"title": "SDD", "description": "Consulta lo stato del tuo mandato di addebito diretto SEPA.", "icon": "🏦", "action_id": "sdd_cons"},
                {"title": "Trasferimenti da altri fondi", "description": "Consulta lo storico dei trasferimenti in entrata.", "icon": "🔄", "action_id": "trasferimenti"},
                {"title": "Scelta investimento dei contributi", "description": "Visualizza la ripartizione storica dei tuoi comparti.", "icon": "📈", "action_id": "scelta_investimento"},
                {"title": "Rendita", "description": "Calcola o visualizza i dettagli della rendita maturata.", "icon": "🪙", "action_id": "rendita"},
                {"title": "Altre posizioni nello stesso prodotto", "description": "Accedi ad altre posizioni attive collegate.", "icon": "💼", "action_id": "altre_posizioni"}
            ]
            policy_info = cached_policy_info or {
                "policy_number": cached_policy or "",
                "policy_name": "Insieme",
                "status": "Attiva",
                "full_name": "Nome Assicurato",
                "agency": "Agenzia Allianz"
            }
            session["user_data"] = {
                "policy": policy_info,
                "operations": operations,
                "consultazioni": consultazioni
            }
            return jsonify({"success": True})
        else:
            print("[*] Cached session is inactive/expired.")

    res, s_obj = run_allianz_scrape(username, password)
    
    if res.get("success"):
        session_key = str(uuid.uuid4())
        active_sessions[session_key] = s_obj
        session["session_key"] = session_key
        
        # Save the ticket URL to Flask session for deferred consumption
        if res.get("ticket_url"):
            session["pending_ticket_url"] = res["ticket_url"]
            
        save_session_to_disk(session_key, s_obj, username, res["policy"]["policy_number"], res["policy"])
        # Store in flask secure cookie session
        session["user_data"] = {
            "policy": res["policy"],
            "operations": res["operations"],
            "consultazioni": res["consultazioni"]
        }
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": res.get("error", "Failed to login.")})


def get_active_session():
    if "session_key" not in session:
        return None
    s_key = session["session_key"]
    if s_key not in active_sessions:
        saved_data = load_session_from_disk()
        saved_key = saved_data[0]
        saved_s = saved_data[1]
        if saved_key == s_key and saved_s:
            active_sessions[s_key] = saved_s
        else:
            return None
    return active_sessions[s_key]


def extract_main_content(html_content, current_path):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Try to find the main layout content cell (width="85%")
    content_block = soup.find('td', width='85%')
    
    # 2. Fall back to form
    if not content_block:
        content_block = soup.find('form')
        
    # 3. Fall back to the defaultPage table
    if not content_block:
        content_block = soup.find('table', class_='defaultPage')
        
    # 4. Fall back to body
    if not content_block:
        content_block = soup.find('body')
        
    if not content_block:
        content_block = soup

    # Clean up absolute legacy colors and layouts to match dark theme
    for tag in content_block.find_all(style=True):
        style_rules = tag['style'].split(';')
        cleaned_rules = []
        for rule in style_rules:
            if ':' in rule:
                key, val = rule.split(':', 1)
                key = key.strip().lower()
                if key not in ['background', 'background-color', 'color', 'font-family', 'font-size', 'height', 'width']:
                    cleaned_rules.append(rule)
        tag['style'] = ';'.join(cleaned_rules)
        
    for tag in content_block.find_all():
        if tag.has_attr('bgcolor'):
            del tag['bgcolor']
        if tag.has_attr('color') and tag.name != 'font':
            del tag['color']
        if tag.has_attr('width'):
            del tag['width']
        if tag.has_attr('height'):
            del tag['height']
            
    # Clean up empty paragraphs, empty table rows, divs, spans, and empty line breaks to remove large legacy spaces
    for tag in content_block.find_all(['p', 'div', 'tr', 'span', 'br']):
        txt = tag.get_text(strip=True).replace('\xa0', '')
        if not txt and not tag.find_all(['img', 'input', 'button', 'a']):
            tag.decompose()
    for tag in content_block.find_all(href=True):
        href = tag['href']
        if not href.startswith('#') and not href.startswith('javascript:') and not href.startswith('http'):
            resolved = urljoin(current_path, href)
            tag['href'] = f"/proxy{resolved}"
            
    for tag in content_block.find_all(src=True):
        src = tag['src']
        if not src.startswith('http'):
            resolved = urljoin(current_path, src)
            tag['src'] = f"/proxy{resolved}"
        
    for tag in content_block.find_all(action=True):
        action = tag['action']
        if not action.startswith('http'):
            resolved = urljoin(current_path, action)
            tag['action'] = f"/proxy{resolved}"
            
    # Translate blank values in inputs and button tags (styled as background-images in legacy CSS)
    BUTTON_TRANSLATIONS = {
        "salva": "Salva",
        "conferma": "Conferma",
        "conferma2": "Conferma",
        "conferma3": "Conferma",
        "seleziona": "Seleziona",
        "annullaSelezione": "Annulla",
        "annullaselezione": "Annulla",
        "annulla": "Annulla",
        "modifica": "Modifica",
        "inserisci": "Inserisci",
        "indietro": "Indietro",
        "prosegui": "Prosegui ➔",
        "prosegui2": "Prosegui ➔",
        "prosegui3": "Prosegui ➔",
        "calcola": "Calcola",
        "ricerca": "Cerca",
        "cerca": "Cerca",
        "cerca2": "Cerca",
        "cerca3": "Cerca",
        "stampa": "Stampa ⎙",
        "stampa2": "Stampa ⎙",
        "stampa3": "Stampa ⎙",
        "avanti": "Avanti ➔",
        "invia": "Invia ➔",
        "invia2": "Invia ➔",
        "invia3": "Invia ➔",
        "accedi": "Accedi",
        "aggiorna": "Aggiorna"
    }
    
    for btn in content_block.find_all(['input', 'button']):
        is_input = (btn.name == 'input')
        btn_type = btn.get('type', '').lower() if is_input else ''
        
        # Translate submit, button, image inputs, and inputs with no type (defaults to text/submit)
        if is_input and btn_type not in ['submit', 'button', 'image', '']:
            continue
            
        val = btn.get('value', '')
        if val is None:
            val = ''
        val = str(val).strip()
        
        if not val or val == '.':
            classes = btn.get('class', [])
            translated = None
            for cls in classes:
                if cls in BUTTON_TRANSLATIONS:
                    translated = BUTTON_TRANSLATIONS[cls]
                    break
            
            # Substring fallback matching inside class names
            if not translated:
                for cls in classes:
                    cls_lower = cls.lower()
                    if "cerca" in cls_lower or "ricerca" in cls_lower:
                        translated = "Cerca"
                    elif "stampa" in cls_lower:
                        translated = "Stampa ⎙"
                    elif "salva" in cls_lower:
                        translated = "Salva"
                    elif "conferma" in cls_lower:
                        translated = "Conferma"
                    elif "annulla" in cls_lower:
                        translated = "Annulla"
                    elif "indietro" in cls_lower:
                        translated = "Indietro"
                    elif "prosegui" in cls_lower:
                        translated = "Prosegui ➔"
                    elif "avanti" in cls_lower:
                        translated = "Avanti ➔"
                    elif "invia" in cls_lower:
                        translated = "Invia ➔"
                    elif "inserisci" in cls_lower:
                        translated = "Inserisci"
                    elif "modifica" in cls_lower:
                        translated = "Modifica"
                    elif "calcola" in cls_lower:
                        translated = "Calcola"
                    elif "seleziona" in cls_lower:
                        translated = "Seleziona"
                    if translated:
                        break
            
            # Substring fallback matching inside image src attribute
            if not translated:
                src_val = btn.get("src", "")
                if src_val:
                    src_lower = src_val.lower()
                    if "cerca" in src_lower or "ricerca" in src_lower:
                        translated = "Cerca"
                    elif "stampa" in src_lower:
                        translated = "Stampa ⎙"
                    elif "salva" in src_lower:
                        translated = "Salva"
                    elif "conferma" in src_lower:
                        translated = "Conferma"
                    elif "annulla" in src_lower:
                        translated = "Annulla"
                    elif "indietro" in src_lower:
                        translated = "Indietro"
                    elif "prosegui" in src_lower:
                        translated = "Prosegui ➔"
                    elif "avanti" in src_lower:
                        translated = "Avanti ➔"
                    elif "invia" in src_lower:
                        translated = "Invia ➔"
                    elif "inserisci" in src_lower:
                        translated = "Inserisci"
                    elif "modifica" in src_lower:
                        translated = "Modifica"
                    elif "calcola" in src_lower:
                        translated = "Calcola"
                    elif "seleziona" in src_lower:
                        translated = "Seleziona"

            if translated:
                if is_input:
                    btn["value"] = translated
                    if btn_type in ["image", ""]:
                        btn["type"] = "submit"
                else:
                    btn.string = translated
                        
    return str(content_block)


def get_submenu_items(soup, current_path):
    submenu_items = []
    menu_table = soup.find('table', id='menu')
    if not menu_table:
        return submenu_items
        
    menuhere_td = menu_table.find(id='menuhere')
    if not menuhere_td:
        return submenu_items
        
    active_tr = menuhere_td.find_parent('tr')
    if not active_tr:
        return submenu_items
        
    # Find the main menu item tr (the one with colspan="2" on its td)
    main_menu_tr = None
    td = active_tr.find('td')
    if td and td.get('colspan') == '2':
        main_menu_tr = active_tr
    else:
        # Traverse backwards to find the main menu header tr
        prev = active_tr.find_previous_sibling('tr')
        while prev:
            prev_td = prev.find('td')
            if prev_td and prev_td.get('colspan') == '2':
                main_menu_tr = prev
                break
            prev = prev.find_previous_sibling('tr')
            
    if not main_menu_tr:
        main_menu_tr = active_tr
        
    # Now traverse forward from main_menu_tr to collect all sub-menu items
    for sibling in main_menu_tr.find_next_siblings('tr'):
        sib_td = sibling.find('td')
        if not sib_td:
            continue
        # Stop when we reach the next main menu item
        if sib_td.get('colspan') == '2':
            break
            
        a = sib_td.find('a')
        is_active_item = (sib_td.get('id') == 'menuhere') or (a and a.get('id') == 'menuhere')
        
        text = ""
        href = ""
        if a:
            href = a.get('href', '')
            text = a.get_text(strip=True)
        else:
            text = sib_td.get_text(strip=True)
            
        if text.startswith('-'):
            text = text[1:].strip()
            
        if href:
            if not href.startswith('#') and not href.startswith('javascript:') and not href.startswith('http'):
                resolved = urljoin(current_path, href)
                proxied_url = f"/proxy{resolved}"
            else:
                proxied_url = href
        else:
            proxied_url = "#"
            
        submenu_items.append({
            "text": text,
            "url": proxied_url,
            "active": is_active_item
        })
    return submenu_items


def is_menu_matching(soup, url):
    is_consultazione = False
    if "user_data" in session and 'active_operation_id' in session:
        is_consultazione = (session['active_operation_id'] in CONSULTAZIONI_ACTION_IDS)
    else:
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(url)
        method_param = parse_qs(parsed_url.query).get('method', [''])[0]
        
        for act_id in CONSULTAZIONI_ACTION_IDS:
            target = ACTIONS.get(act_id)
            if target:
                target_method = parse_qs(urlparse(target).query).get('method', [''])[0]
                if target_method == method_param:
                    is_consultazione = True
                    break
        if method_param == "consultazioni":
            is_consultazione = True
        elif method_param == "operazioni":
            is_consultazione = False
        
    menu_table = soup.find('table', id='menu')
    if not menu_table:
        return False
        
    menu_text = menu_table.get_text()
    if is_consultazione:
        return "Cessione del Quinto" in menu_text or "Estratto conto" in menu_text
    else:
        return "Beneficiari" in menu_text or "Cambio Azienda" in menu_text


def fetch_page_with_menu(s, url, headers=None, method="GET", data=None, params=None, allow_redirects=True):
    # Consume deferred ticket if present
    if "pending_ticket_url" in session:
        ticket_url = session.pop("pending_ticket_url")
        print(f"[*] Consuming deferred security ticket: {ticket_url}")
        try:
            ticket_headers = {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            }
            ticket_res = s.get(ticket_url, headers=ticket_headers, allow_redirects=True, timeout=15)
            if ticket_res.status_code != HTTP_OK:
                print(f"[!] Warning: Failed to consume deferred security ticket. Status: {ticket_res.status_code}")
        except Exception as e:
            print(f"[!] Error consuming deferred security ticket: {str(e)}")

    if method == "POST":
        res = s.post(url, data=data, params=params, headers=headers, allow_redirects=allow_redirects, timeout=15)
    else:
        res = s.get(url, params=params, headers=headers, allow_redirects=allow_redirects, timeout=15)
        
    content_type = res.headers.get("Content-Type", "")
    if "text/html" in content_type:
        text_lower = res.text.lower()
        if any(marker in text_lower for marker in ["spiacenti", "passato troppo tempo", "disconnesso"]):
            raise SessionExpiredException("Session expired on Allianz portal.")
            
        soup = BeautifulSoup(res.text, 'html.parser')
        if not is_menu_matching(soup, url):
            is_consultazione = False
            if "user_data" in session and 'active_operation_id' in session:
                is_consultazione = (session['active_operation_id'] in CONSULTAZIONI_ACTION_IDS)
            else:
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(url)
                method_param = parse_qs(parsed_url.query).get('method', [''])[0]
                for act_id in CONSULTAZIONI_ACTION_IDS:
                    target = ACTIONS.get(act_id)
                    if target:
                        target_method = parse_qs(urlparse(target).query).get('method', [''])[0]
                        if target_method == method_param:
                            is_consultazione = True
                            break
                if method_param == "consultazioni":
                    is_consultazione = True
                elif method_param == "operazioni":
                    is_consultazione = False
                    
            init_url = "https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuHigh.do?method=consultazioni" if is_consultazione else OPERATIONS_URL
            print(f"[*] Menu empty or mismatch on {url}. Re-initializing J2EE session menu state using {init_url}...")
            s.get(init_url, headers=headers, timeout=15)
            
            if method == "POST":
                res = s.post(url, data=data, params=params, headers=headers, allow_redirects=allow_redirects, timeout=15)
            else:
                res = s.get(url, params=params, headers=headers, allow_redirects=allow_redirects, timeout=15)
                
            # Check the second response as well just in case
            content_type = res.headers.get("Content-Type", "")
            if "text/html" in content_type:
                text_lower = res.text.lower()
                if any(marker in text_lower for marker in ["spiacenti", "passato troppo tempo", "disconnesso"]):
                    raise SessionExpiredException("Session expired on Allianz portal.")
    return res


def render_operation_view(title, content, parent_description=None, submenu_items=None, back_url=None, is_landing_page=False):
    # Determine if there is meaningful content to display in the card
    show_content_card = True
    parent_description_open = False
    
    if parent_description and content:
        # Check if content has visible text or elements
        soup_check = BeautifulSoup(content, 'html.parser')
        
        # 1. Decompose elements that are hidden by our CSS
        for tag in soup_check.find_all(class_=['headerPage', 'headerPageMid', 'headerPageRight', 'headerPageLeft']):
            tag.decompose()
            
        # 2. Decompose help images and help links
        for tag in soup_check.find_all('img'):
            src = tag.get('src', '').lower()
            if 'help' in src:
                tag.decompose()
                
        for tag in soup_check.find_all('a'):
            href = tag.get('href', '').lower()
            onclick = tag.get('onclick', '').lower()
            if 'openhelpwindow' in href or 'openhelpwindow' in onclick or 'javascript:openhelpwindow' in href or 'javascript:openhelpwindow' in onclick:
                tag.decompose()
                
        # Find any inputs that are NOT hidden
        visible_inputs = soup_check.find_all(lambda tag: tag.name == 'input' and tag.get('type') != 'hidden')
        other_visible = soup_check.find_all(['button', 'select', 'textarea', 'img', 'a'])
        
        # If there are no inputs and no other interactive/meaningful elements
        if not visible_inputs and not other_visible:
            show_content_card = False
            parent_description_open = True
            
    elif parent_description and not content:
        show_content_card = False
        parent_description_open = True

    return render_template(
        "operation.html",
        title=title,
        content=content,
        parent_description=parent_description,
        submenu_items=submenu_items or [],
        back_url=back_url,
        is_landing_page=is_landing_page,
        show_content_card=show_content_card,
        parent_description_open=parent_description_open
    )


@app.route("/section/<section_id>")
def section_view(section_id):
    if "user_data" not in session:
        return redirect(url_for("index"))
        
    get_active_session()
    
    if section_id == "consultazioni":
        section_title = "Consultazioni"
        items = session["user_data"].get("consultazioni", [])
    elif section_id == "operazioni":
        section_title = "Operazioni Disponibili"
        items = session["user_data"].get("operations", [])
    else:
        return "Invalid section", 400
        
    return render_template("section.html", section_title=section_title, items=items, policy=session["user_data"]["policy"])


@app.route("/operation/<action_id>")
def operation_view(action_id):
    if "user_data" not in session:
        return redirect(url_for("index"))
        
    s = get_active_session()
    if not s:
        return redirect(url_for("index"))
    target_url = ACTIONS.get(action_id)
    if not target_url:
        return "Invalid operation", 400
        
    # Get Title
    op_title = "Operazione"
    for op in session["user_data"].get("operations", []):
        if op["action_id"] == action_id:
            op_title = op["title"]
            break
    if op_title == "Operazione":
        for op in session["user_data"].get("consultazioni", []):
            if op["action_id"] == action_id:
                op_title = op["title"]
                break
                
    # Save active operation context
    session['active_operation_id'] = action_id
    session['active_operation_title'] = op_title
            
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    section_back_url = url_for("section_view", section_id="consultazioni") if action_id in CONSULTAZIONI_ACTION_IDS else url_for("section_view", section_id="operazioni")
    
    try:
        res = fetch_page_with_menu(s, target_url, headers=headers)
        if res.status_code != HTTP_OK:
            return f"Error loading operation. Status: {res.status_code}", 500
            
        # Save for debugging
        with open(f"{action_id}_raw.html", "w", encoding="utf-8") as f:
            f.write(res.text)
            
        current_path = "/UnifondiRASNP/priv/"
        soup_res = BeautifulSoup(res.text, 'html.parser')
        submenu_items = get_submenu_items(soup_res, current_path)
        
        # Save landing flag to session
        session['active_operation_is_landing'] = (len(submenu_items) > 1)
        
        # Scenario A: Single Submenu Item -> Load the sub-action content directly
        if len(submenu_items) == 1:
            sub_item = submenu_items[0]
            # Convert proxy URL back to target J2EE URL
            sub_url = sub_item['url']
            if sub_url.startswith('/proxy/'):
                sub_url = sub_url.replace('/proxy/', 'https://previdenzacomplementare.allianz.it/')
            elif sub_url.startswith('/'):
                sub_url = f"https://previdenzacomplementare.allianz.it{sub_url}"
                
            res_sub = fetch_page_with_menu(s, sub_url, headers=headers)
            if res_sub.status_code == HTTP_OK:
                parent_description = extract_main_content(res.text, current_path)
                sub_content = extract_main_content(res_sub.text, current_path)
                return render_operation_view(title=op_title, content=sub_content, parent_description=parent_description, submenu_items=[], back_url=section_back_url, is_landing_page=False)
                
        # Scenario B: Multiple Submenu Items -> Render operation landing page with choice cards
        if len(submenu_items) > 1:
            parent_description = extract_main_content(res.text, current_path)
            # Differentiate the cards with classes & icons
            differentiated_submenu = []
            for item in submenu_items:
                text = item['text']
                # Determine icon and card type based on text
                card_type = "consultazioni-card"
                icon = "🔍"
                if any(x in text.lower() for x in ["modifica", "inserisci", "variazione", "cambio", "richiesta"]):
                    card_type = "operazioni-card"
                    icon = "⚙️"
                differentiated_submenu.append({
                    "text": text,
                    "url": item['url'],
                    "active": item['active'],
                    "card_type": card_type,
                    "icon": icon
                })
            return render_operation_view(title=op_title, content=None, parent_description=parent_description, submenu_items=differentiated_submenu, back_url=section_back_url, is_landing_page=True)
            
        # Default fallback (0 submenu items)
        content_html = extract_main_content(res.text, current_path)
        return render_operation_view(title=op_title, content=content_html, submenu_items=submenu_items, back_url=section_back_url, is_landing_page=False)
        
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/proxy/<path:subpath>", methods=["GET", "POST"])
def proxy(subpath):
    s = get_active_session()
    if not s:
        return redirect(url_for("index"))
    target_url = f"https://previdenzacomplementare.allianz.it/{subpath}"
    
    params = request.args
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": request.headers.get("Accept"),
        "Accept-Language": request.headers.get("Accept-Language")
    }
    
    # Determine back_url based on active operation in session
    back_url = None
    if session.get('active_operation_is_landing') and 'active_operation_id' in session:
        back_url = url_for('operation_view', action_id=session['active_operation_id'])
    else:
        # Fallback to category section
        is_consultazione = False
        for act_id in CONSULTAZIONI_ACTION_IDS:
            target = ACTIONS.get(act_id)
            if target and target.split("method=")[-1] in request.url:
                is_consultazione = True
                break
        back_url = url_for("section_view", section_id="consultazioni") if is_consultazione else url_for("section_view", section_id="operazioni")
    
    try:
        res = fetch_page_with_menu(s, target_url, headers=headers, method=request.method, data=request.form, params=params, allow_redirects=False)
            
        if res.status_code in [301, 302, 303, 307, 308]:
            redirect_url = res.headers.get("Location")
            resolved_redirect = urljoin(target_url, redirect_url)
            if "previdenzacomplementare.allianz.it" in resolved_redirect:
                path_part = resolved_redirect.split("previdenzacomplementare.allianz.it")[-1]
                return redirect(f"/proxy{path_part}")
            return redirect(resolved_redirect)
            
        content_type = res.headers.get("Content-Type", "")
        if "text/html" in content_type:
            current_path = f"/{subpath}"
            content_html = extract_main_content(res.text, current_path)
            soup_res = BeautifulSoup(res.text, 'html.parser')
            submenu_items = get_submenu_items(soup_res, current_path)
            # Render top submenu bar if there are multiple sub-options
            render_submenu = submenu_items if len(submenu_items) > 1 else []
            return render_operation_view(title=session.get('active_operation_title', 'Dettaglio Operazione'), content=content_html, submenu_items=render_submenu, back_url=back_url, is_landing_page=False)
            
        return res.content, res.status_code, {"Content-Type": content_type}
    except Exception as e:
        return f"Proxy error: {str(e)}", 500


@app.route("/UnifondiRASNP/<path:subpath>", methods=["GET", "POST"])
def ras_proxy(subpath):
    return proxy(f"UnifondiRASNP/{subpath}")


@app.route("/logout")
def logout():
    session.clear()
    try:
        if os.path.exists("session_cache.pkl"):
            os.remove("session_cache.pkl")
    except:
        pass
    return redirect(url_for("index"))


@app.route("/debug/save_all_pages")
def debug_save_all_pages():
    if not active_sessions:
        saved_data = load_session_from_disk()
        saved_key = saved_data[0]
        saved_s = saved_data[1]
        if saved_key and saved_s:
            active_sessions[saved_key] = saved_s
        else:
            return "No active sessions in memory!", 404
    s = list(active_sessions.values())[0]
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    results = []
    for action_id, url in ACTIONS.items():
        try:
            res = s.get(url, headers=headers)
            with open(f"{action_id}_raw.html", "w", encoding="utf-8") as f:
                f.write(res.text)
            results.append(f"{action_id} saved successfully")
        except Exception as e:
            results.append(f"{action_id} failed: {str(e)}")
    return "<br>".join(results)


if __name__ == "__main__":
    # Run locally on all network interfaces (allows mobile access on same local Wi-Fi)
    app.run(host="0.0.0.0", port=5000, debug=True)
