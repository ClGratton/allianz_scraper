# Allianz Web Scraper e Client Proxy

Questa applicazione fornisce una interfaccia web moderna per interagire con il portale Allianz Previdenza. Agisce come un intermediario intelligente, effettuando lo scraping in tempo reale delle pagine J2EE protette del portale Allianz e ripresentando i dati all'utente in modo chiaro, pulito e integrato con il tema grafico preferito.

## Caratteristiche Principali

* Login Rapido e Ottimizzato: Esegue una richiesta diretta POST per autenticare l'utente, riducendo i tempi di caricamento del cinquanta per cento.
* Cache di Sessione: Memorizza in modo cifrato e sicuro la sessione sul disco locale per evitare la ripetizione dei passaggi di login.
* Riconoscimento Timeout: Rileva automaticamente se la sessione sul portale Allianz è scaduta e reindirizza l'utente alla schermata di login.
* Interfaccia Responsive: Riorganizza i dati legacy in griglie moderne, tabelle pulite e schede informative.
* Tema Scuro: Supporto nativo per il cambio del tema visivo memorizzato localmente.

---

## Flusso Chiamate Portale Allianz (Sotto il cofano)

Il portale Allianz utilizza una serie di passaggi sequenziali tra domini diversi per autenticare l'utente e stabilire lo stato della sessione previdenziale.

### 1. Autenticazione (Area Personale)
L'accesso iniziale avviene sul dominio dell'Area Personale Allianz.
* URL: `https://areapersonale.allianz.it/digitalme/public/login/login%2Dfilter.do`
* Metodo: POST
* Payload:
  j_username = [email utente]
  j_password = [password]
  login = Accedi
* Cookie rilasciati: SMSESSION (cookie di sessione principale per il portale clienti)

### 2. Estrazione Link Dettaglio Polizza
Una volta autenticato, il client richiede la pagina della dashboard della polizza specifica.
* URL: `https://areapersonale.allianz.it/digitalme/private/detailDigMe.do?numeroPolizza=[numero_polizza]&attivi=1`
* Metodo: GET
* Funzione: La pagina caricata contiene un link dinamico (AJAX tab) all'interno di un tag ancorato con attributo data_toggle (attributo data per i tab) pari a "tabajax". Questo link punta al dettaglio previdenziale della polizza.

### 3. Recupero del Ticket di Sicurezza (SCA)
Il client effettua una richiesta GET verso il link AJAX individuato nel passo precedente.
* Metodo: GET
* Funzione: Ritorna una pagina HTML contenente il link di transizione del dominio per la previdenza complementare. Questo link contiene un ticket di sicurezza monouso:
  `https://previdenzacomplementare.allianz.it/UnifondiRASNP/asso/actionAttestationSCAInit.do?ticket=[valore_ticket]`

### 4. Transizione Dominio e Consumo Ticket
Il client effettua una chiamata GET alla URL del ticket sul dominio previdenziale.
* Metodo: GET
* Funzione: Il server Allianz convalida il ticket di sicurezza e rilascia il cookie di sessione J2EE per l'area previdenza complementare.
* Cookie rilasciati: JSESSIONID (sul dominio previdenzacomplementare.allianz.it)

### 5. Inizializzazione del Menu J2EE
L'applicazione previdenziale Allianz (UnifondiRASNP) richiede che lo stato del menu del server sia inizializzato prima di poter navigare le singole operazioni.
* URL per Operazioni: `https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuHigh.do?method=operazioni`
* URL per Consultazioni: `https://previdenzacomplementare.allianz.it/UnifondiRASNP/priv/actionMenuHigh.do?method=consultazioni`
* Funzione: Se si tenta di accedere a una pagina di operazione (es. SDD) senza avant visitato la URL di inizializzazione corretta, il server risponde con un errore o una pagina priva di sottomenu.

### 6. Navigazione Operazioni
Le singole schermate vengono caricate tramite chiamate GET.
* Esempio variazione SDD: `/UnifondiRASNP/priv/actionMenuLeft.do?method=variazioneSDD`
* Sottomenu dinamico: La pagina principale di una operazione può contenere un elenco di sotto_operazioni (es. `method=isInserimentoSDD`). Se è presente una sola sotto_operazione, l'applicazione proxy carica direttamente quest'ultima per semplificare l'interfaccia.

### 7. Gestione della Scadenza Sessione
Allianz gestisce il timeout della sessione restituendo una pagina HTML con codice di stato 200 OK contenente il testo "Siamo spiacenti ma e' passato troppo tempo...". Il proxy analizza ogni risposta HTML per intercettare questa stringa, distruggendo la cache locale e forzando il reindirizzamento al login in caso di riscontro.

---

## Requisiti di Sistema

* Python versione 3.12 o superiore
* Connessione internet attiva per comunicare con i server Allianz

Librerie Python richieste:
* Flask (gestione del server web)
* Requests (comunicazione HTTP)
* BeautifulSoup4 (analisi e manipolazione dell'HTML)

---

## Installazione e Avvio

1. Installare i pacchetti Python necessari:
   pip install flask requests beautifulsoup4

2. Avviare il server locale:
   python app.py

3. Navigare all'indirizzo locale:
   http://127.0.0.1:5000

---

## Riferimento API e Rotte del Proxy Locale

### GET /
Ritorna la pagina iniziale con il form di login.

### POST /api/login
Roteazione delle credenziali.
* Payload Richiesta (JSON):
  {
    "username": "utente@email.com",
    "password": "la_tua_password",
    "policy_number": "12345678"
  }
* Risposta di Successo (JSON):
  {
    "success": true
  }
* Risposta di Errore (JSON):
  {
    "success": false,
    "error": "Descrizione dell'errore"
  }

### GET /dashboard
Carica la schermata principale dopo l'accesso. Mostra le informazioni generali della polizza.

### GET /section/<section_id>
Filtra e visualizza le voci disponibili.
* Valori validi per section_id: "operazioni", "consultazioni".

### GET /operation/<action_id>
Carica una specifica operazione o consultazione (ad esempio "sdd"). Se l'operazione ha una descrizione e nessun form compilabile, mostra la descrizione aperta ed esclude la scheda di contenuto vuota.

### GET o POST /proxy/<path:subpath>
Rotte di proxying dinamico. Reindirizza le richieste interne verso i server Allianz conservando i cookie e lo stato della sessione.

### GET /logout
Termina la sessione corrente, rimuove il file di cache locale e reindirizza alla home.

---

## Risoluzione dei Problemi

### Sessione Scaduta
Se la sessione Allianz scade per inattività, il server intercetta il messaggio di timeout del portale e reindirizza l'utente alla pagina di accesso in modo pulito.

### Errore di Connessione
Assicurarsi che la macchina locale sia connessa a internet e che i server Allianz siano raggiungibili.
