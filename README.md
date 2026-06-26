# Allianz Web Scraper e Client Proxy

Questa applicazione fornisce una interfaccia web moderna per interagire con il portale Allianz Previdenza. Il documento illustra l'architettura tecnica del portale Allianz, il flusso delle sue chiamate J2EE e le modalità con cui questo proxy replica e ottimizza l'esperienza utente.

## Flusso Chiamate Portale Allianz

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
* Funzione: Se si tenta di accedere a una pagina di operazione (es. SDD) senza aver prima visitato la URL di inizializzazione corretta, il server risponde con un errore o una pagina priva di sottomenu.

### 6. Navigazione Operazioni
Le singole schermate vengono caricate tramite chiamate GET.
* Esempio variazione SDD: `/UnifondiRASNP/priv/actionMenuLeft.do?method=variazioneSDD`
* Sottomenu dinamico: La pagina principale di una operazione può contenere un elenco di sotto_operazioni (es. `method=isInserimentoSDD`). Se è presente una sola sotto_operazione, l'applicazione proxy carica direttamente quest'ultima per semplificare l'interfaccia.

### 7. Gestione della Scadenza Sessione
Allianz gestisce il timeout della sessione restituendo una pagina HTML con codice di stato 200 OK contenente il testo "Siamo spiacenti ma e' passato troppo tempo...". Il proxy analizza ogni risposta HTML per intercettare questa stringa, distruggendo la cache locale e forzando il reindirizzamento al login in caso di riscontro.

## Struttura dell'Applicazione Proxy

L'applicazione locale replica questo comportamento offrendo le seguenti rotte:

* POST /api/login : Riceve le credenziali ed esegue i passi da 1 a 4. Salva la sessione in un file locale chiamato `session_cache.pkl` per evitare di ripetere l'autenticazione.
* GET /dashboard : Mostra i dati generali della polizza.
* GET /section/<section_id> : Mostra le voci disponibili per la sezione selezionata.
* GET /operation/<action_id> : Esegue l'inizializzazione del menu (passo 5) e carica l'operazione richiesta. Se la pagina contiene solo la descrizione senza form operativi, espande la descrizione e nasconde la scheda vuota.
* GET o POST /proxy/<path:subpath> : Gestisce in modo trasparente l'inoltro delle chiamate al dominio previdenziale Allianz mantenendo i cookie e lo stato aggiornato.
