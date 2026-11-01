# CoachFlow 🏋️‍♂️🤖

> **Open-Source AI Assistant on WhatsApp for Personal Trainers and Fitness Coaches.**  
> Fissa appuntamenti, dialoga con i lead, sincronizza i calendari e azzera i no-show con promemoria interattivi.

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![Framework](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API%20Official-25D366.svg)](https://developers.facebook.com/docs/whatsapp/cloud-api)

---

## 🌟 Caratteristiche Principali

- 🎙️ **Discovery Outreach con Nota Vocale:** Primo contatto personalizzato che invia una vera nota audio registrata dal Personal Trainer (formato nativo WhatsApp OGG/Opus).
- 📅 **Conversational Booking & Calendar Sync:** L'AI conversa amichevolmente con il lead/cliente, consulta in tempo reale **Google Calendar** (o altri calendari modulari) e prenota gli slot liberi evitando sovrapposizioni.
- ✅ **Zero No-Show con Bottoni WhatsApp:** Promemoria automatici a T-24h e T-2h con pulsanti interattivi (`Confermo ✅`, `Sposta 🔄`, `Annulla ❌`). Le risposte deterministiche non consumano token AI (costo = 0€).
- 🛎️ **Daily Digest per il Coach:** Ricevi ogni mattina su WhatsApp la lista degli atleti del giorno e un promemoria 30 minuti prima di ciascuna sessione.
- 🛡️ **Canale Ufficiale Meta:** Zero rischi di ban del numero, supporto a template pre-approvati e piena conformità GDPR.
- 🔌 **Architettura Modulare:** Interfacce astratte per Calendar Provider (`GoogleCalendar`, `Cal.com`, `Apple`) e AI Provider (`OpenAI`, `Gemini`).
- 🗄️ **Persistenza Asincrona:** Supporto completo a SQLAlchemy 2.0 Async con switch immediato tra SQLite (sviluppo) e PostgreSQL (produzione).
- 💻 **Web Dashboard per il Coach:** Interfaccia reattiva e leggera (`/dashboard`) per monitorare atleti, gestire i turni settimanali, bloccare slot personali e mettere in pausa l'AI con 1 click.
- 🛡️ **Motore Anti-Conflitto a 3 Livelli:** Protezione automatica dei tempi di allenamento personale, turni spezzati e pause del coach (con sync istantaneo di eventi personali da Google Calendar dallo smartphone).
- 🐳 **Containerizzazione Multi-Stage Ultra-Slim:** Immagine Docker minimale conforme alle best practice di sicurezza (build multi-stage senza layer intermedi di compilazione, utente non-root `coachflow`, healthcheck integrato).

---

## 🏛️ Architettura di Sistema

```mermaid
flowchart TD
    Lead([Prospect / Atleta]) <-->|WhatsApp| MetaAPI[Meta WhatsApp Cloud API]
    MetaAPI <--> Webhook[FastAPI Webhook Handler]
    
    subgraph Core Engine
        Router{Hybrid Message Router}
        Router -->|Bottoni/Keywords (0€)| DetEngine[Deterministic Handler]
        Router -->|Testo Libero / Negoziazione| AIAgent[AI Conversational Agent]
    end
    
    Webhook <--> Router
    
    subgraph Modular Providers
        CalProvider[Calendar Provider (Google Calendar / Cal.com)]
        Scheduler[Background Scheduler (T-24h, T-2h, Daily Digest)]
    end
    
    AIAgent <--> CalProvider
    DetEngine <--> CalProvider
    Scheduler --> MetaAPI
```

---

## 🚀 Avvio Rapido (Quickstart)

### 1. Clonazione e Ambiente Virtuale
```bash
git clone https://github.com/marcorotella/coach-flow.git
cd coach-flow
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configurazione Variabili d'Ambiente
```bash
cp .env.example .env
# Compila le credenziali Meta WhatsApp e Calendar nel file .env
```

### 3. Avvio del Server di Sviluppo
```bash
uvicorn coach_flow.main:app --reload --port 8000
```

---

## 🐳 Avvio con Docker & Docker Compose (Produzione)

L'applicazione include un `Dockerfile` multi-stage moderno e ottimizzato:
- **Build stage isolato:** I compilatori (`gcc`, `build-essential`) e la cache pip vengono scartati e non finiscono mai nell'immagine finale.
- **Runtime stage minimale:** Basato su Debian Bookworm slim con le sole dipendenze di runtime essenziali (`curl`, `ca-certificates`, `libpq5`).
- **Sicurezza:** Esecuzione sotto utente unprivileged non-root (`coachflow:coachflow`, UID 10001).
- **Database PostgreSQL:** Connessione asincrona (`asyncpg`) e verifica dello stato con healthcheck.

### Avvio rapido dello stack (App + PostgreSQL):
```bash
# Avvia PostgreSQL e l'API FastAPI in background
docker compose up -d --build

# Verifica lo stato e gli healthcheck dei container
docker compose ps

# Visualizza i log in streaming
docker compose logs -f app
```

L'API sarà disponibile su `http://localhost:8000` con documentazione interattiva su `http://localhost:8000/docs`.

---

## 📚 Documentazione di Progetto

- [Guida per la Creazione dell'Ambiente di Test (GUIDA_AMBIENTE_TEST.md)](docs/GUIDA_AMBIENTE_TEST.md)
- [Manuale Pratico per il Personal Trainer (GUIDA_UTENTE_COACH.md)](docs/GUIDA_UTENTE_COACH.md)
- [Specifiche Funzionali e Tecniche Complete](docs/SPECIFICATIONS.md)
- [Proposta Esecutiva Personal Trainer (PDF)](docs/Proposta_Assistente_AI_Personal_Trainer.pdf)

---

## 🤝 Contribuzione

I contributi sono benvenuti! Leggi la [Guida alla Contribuzione (CONTRIBUTING.md)](CONTRIBUTING.md) per scoprire come aprire Issue, inviare Pull Request e rispettare gli standard del codice.

---

## ⚖️ Licenza

Questo progetto è distribuito sotto licenza **MIT**. Consulta il file [LICENSE](LICENSE) per i dettagli.
