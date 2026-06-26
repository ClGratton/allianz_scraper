# Scraper e Proxy Allianz

Questo progetto realizza una interfaccia web moderna per consultare ed effettuare operazioni sulla propria posizione previdenziale Allianz. L'applicazione agisce come un client dinamico che interagisce con il portale Allianz in tempo reale.

## Come Funziona

L'applicazione si basa su una architettura composta da diversi moduli:

1. Autenticazione: L'utente inserisce le proprie credenziali email, password e numero di polizza. L'applicazione esegue una chiamata POST direttamente verso il portale Allianz per ottenere i cookie di sessione.
2. Salvataggio Sessione: Per velocizzare gli accessi successivi, i cookie e le informazioni di sessione attive vengono serializzati sul disco locale in un file di cache.
3. Transizione del Dominio: Il portale Allianz utilizza dei ticket di sicurezza per autorizzare la navigazione sul portale interno della previdenza complementare. L'applicazione cattura ed elabora questi ticket in modo automatico.
4. Proxying delle Operazioni: Ogni pagina interna viene scaricata, privata degli elementi non necessari o stilizzati in modo obsoleto, e renderizzata all'interno di una interfaccia web moderna e responsive.

## Requisiti

* Python versione 3.12 o superiore
* Pip per la gestione delle librerie Python

## Installazione

1. Installare le librerie necessarie:
   pip install flask requests beautifulsoup4

2. Avviare l'applicazione web:
   python app.py

3. Aprire il browser web e navigare alla pagina:
   http://127.0.0.1:5000

## Rotte e API Principali

* GET / : Schermata di login iniziale
* POST /api/login : Riceve le credenziali ed effettua l'accesso sul portale Allianz
* GET /dashboard : Mostra il riepilogo della polizza e le categorie di navigazione
* GET /section/<section_id> : Mostra l'elenco delle operazioni o consultazioni disponibili
* GET /operation/<action_id> : Carica la pagina specifica di una operazione o consultazione
* GET/POST /proxy/<path:subpath> : Gestisce le chiamate e le sottomissioni dei form interni del portale Allianz
* GET /logout : Cancella la sessione locale e disconnette l'utente
