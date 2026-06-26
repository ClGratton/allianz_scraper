# Allianz Web Scraper e Client Proxy

Questa applicazione fornisce una interfaccia web moderna, responsive e ad alte prestazioni per interagire con la propria posizione previdenziale Allianz. Agisce come un intermediario intelligente, effettuando lo scraping in tempo reale delle pagine J2EE protette del portale Allianz e ripresentando i dati all'utente in modo chiaro, pulito e integrato con il tema grafico preferito.

## Caratteristiche Principali

* Login Rapido e Ottimizzato: Esegue una richiesta diretta POST per autenticare l'utente, riducendo i tempi di caricamento del cinquanta per cento.
* Cache di Sessione: Memorizza in modo cifrato e sicuro la sessione sul disco locale per evitare la ripetizione dei passaggi di login.
* Riconoscimento Timeout: Rileva automaticamente se la sessione sul portale Allianz è scaduta e reindirizza l'utente alla schermata di login.
* Interfaccia Responsive: Riorganizza i dati legacy in griglie moderne, tabelle pulite e schede informative.
* Tema Scuro: Supporto nativo per il cambio del tema visivo memorizzato localmente.

## Architettura e Flusso Dati

L'applicazione si interpone tra il browser dell'utente e i server Allianz seguendo questo flusso:

1. Autenticazione: L'utente invia le proprie credenziali tramite il form di login locale. L'applicazione invia una richiesta POST a Allianz.
2. Acquisizione Ticket: L'applicazione riceve la risposta, estrae il ticket di sicurezza J2EE (SCA) e lo conserva per consumarlo alla prima richiesta operativa.
3. Parsing e Cleaning: Quando l'utente richiede una risorsa, l'applicazione scarica la pagina originale, rimuove gli stili obsoleti, elimina gli spazi vuoti superflui e adatta il codice HTML.
4. Proxying Dinamico: Tutti i link interni e i form vengono riscritti in modo da transitare attraverso il server proxy locale.

## Requisiti di Sistema

* Python versione 3.12 o superiore
* Connessione internet attiva per comunicare con i server Allianz

Librerie Python richieste:
* Flask (gestione del server web)
* Requests (comunicazione HTTP)
* BeautifulSoup4 (analisi e manipolazione dell'HTML)

## Installazione e Avvio

1. Installare i pacchetti Python necessari:
   pip install flask requests beautifulsoup4

2. Avviare il server locale:
   python app.py

3. Navigare all'indirizzo locale:
   http://127.0.0.1:5000

## Riferimento API e Rotte

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

## Risoluzione dei Problemi

### Sessione Scaduta
Se la sessione Allianz scade per inattività, il server intercetta il messaggio di timeout del portale e reindirizza l'utente alla pagina di accesso in modo pulito.

### Errore di Connessione
Assicurarsi che la macchina locale sia connessa a internet e che i server Allianz siano raggiungibili.
