# CoachFlow - Handover & Status Document 📋

Progetto **CoachFlow** (`coach-flow`): assistente AI per Personal Trainer su WhatsApp (Discovery, Conversational Booking con Tool Calling, Anti No-Show a costo zero-LLM, Trainer Daily Digest e Human Handover).

---

## 📌 Stato del Progetto

- **Nome Progetto:** CoachFlow (`coach-flow`)
- **Repository GitHub:** [https://github.com/marcorotella/coach-flow](https://github.com/marcorotella/coach-flow) (Pubblico, Open Source)
- **Licenza:** MIT
- **Directory di lavoro su `ai-terminal`:** `/home/marco/projects/coach-flow`
- **Ambiente Python:** Python 3.11 con venv in `/home/marco/projects/coach-flow/.venv` (FastAPI, Pydantic, APScheduler, Pytest, Ruff)
- **Stato Test:** **59/59 test passing** (`pytest`), **0 errori o warning di linting** (`ruff check .`)
- **CI Pipeline:** Green su GitHub Actions per tutti i commit e PR su Python 3.10, 3.11 e 3.12.

---

## 📋 Milestones e Issues su GitHub (100% COMPLETATE)

Tutte le milestone e le 10 issue originali del progetto sono state implementate, testate e chiuse con PR verificate in CI:

### Milestone 1: `v0.1.0 - Foundation & Modular Calendar Provider` ✅
- [x] **#1:** Project scaffold, CI/CD, linting and base configuration
- [x] **#2:** Core domain entities & data models (`Trainer`, `Client`, `Lead`, `Appointment`, `TimeSlot`, `WorkingHours`) (Chiusa con PR #11)
- [x] **#3:** Modular Calendar Provider abstraction (`BaseCalendarProvider`, `MockCalendarProvider`, `GoogleCalendarProvider`) (Chiusa con PR #12)

### Milestone 2: `v0.2.0 - WhatsApp Cloud API & Deterministic Engine` ✅
- [x] **#4:** Meta WhatsApp Cloud API client, HMAC SHA-256 signature security & Webhook verification (`/whatsapp/webhook`) (Chiusa con PR #13)
- [x] **#5:** Deterministic interactive button handler (`confirm_*`, `reschedule_*`, `cancel_*`) con zero token LLM e latenza sub-secondo (Chiusa con PR #14)

### Milestone 3: `v0.3.0 - AI Agent & Conversational Booking` ✅
- [x] **#6:** AI Agent Provider abstraction (`BaseAIProvider`, `OpenAIProvider` GPT-4o-mini, `GeminiProvider` Gemini Flash, `MockAIProvider`) (Chiusa con PR #15)
- [x] **#7:** AI Tool Calling (`get_available_slots`, `book_appointment`, `cancel_appointment`, `escalate_to_human`) e `BookingAgent` multi-turn con memoria (Chiusa con PR #16)
- [x] **#8:** Outbound lead outreach con messaggio di benvenuto personalizzato e nota vocale autentica OGG/Opus (`POST /discovery/outreach`) (Chiusa con PR #17)

### Milestone 4: `v0.4.0 - Schedulers & Anti No-Show Automation` ✅
- [x] **#9:** Background reminder scheduler APScheduler per promemoria interattivi T-24h (bottoni rapidi) e finali T-2h (Chiusa con PR #18)
- [x] **#10:** Trainer Daily Digest mattutino con recap agenda e Human Handover alert d'emergenza con link WhatsApp diretto (Chiusa con PR #19)

### Milestone 5: `v0.5.0 - Database Persistence Layer` ✅
- [x] **Persistenza Asincrona con SQLAlchemy 2.0:** Supporto duale per SQLite (`aiosqlite`) in locale e PostgreSQL (`asyncpg`) in produzione.
- [x] **Modelli ORM & Repository Pattern:** `TrainerModel`, `ClientModel`, `AppointmentModel` e `SQLAlchemyRepository` per gestione CRUD atomica (Chiusa con PR #20).

### Milestone 6: `v0.6.0 - Production Containerization & Cloud Readiness` ✅
- [x] **Dockerfile Multi-Stage Ultra-Slim:** Architettura a due stadi (`builder` -> `runner`). Tutti i compilatori (`gcc`, `build-essential`) e la cache pip rimangono isolati nel layer di build e vengono esclusi dall'immagine finale di produzione.
- [x] **Sicurezza & Hardening:** Esecuzione con utente unprivileged `coachflow` (UID 10001), `ca-certificates` per TLS verso Meta/AI APIs, e `HEALTHCHECK` integrato su `/health`.
- [x] **Docker Compose Stack:** Orchestrazione per API e PostgreSQL 16 Alpine con healthcheck (`pg_isready`) e volume persistente.
- [x] **Dockerignore Rigoroso:** Esclusione completa di codice sorgente di test, cache, virtualenv e file di configurazione sensibili.

### Milestone 7: `v0.7.0 - Web Dashboard & Anti-Conflict Availability Engine` ✅
- [x] **Motore di Disponibilità Anti-Conflitto a 3 Livelli:** Protezione algoritmica di turni spezzati, buffer tra sessioni (15m default), pause personali e sync automatico di eventi personali da Google Calendar (es. allenamento del coach).
- [x] **Web Dashboard Integrata (FastAPI + Jinja2 + Tailwind + Alpine.js):**
  - `/dashboard`: Panoramica metrica e sessioni odierne.
  - `/dashboard/working-hours`: Editor turni settimanali spezzati e buffer.
  - `/dashboard/calendar`: Visualizzazione agenda e blocco rapido orari.
  - `/dashboard/clients`: Elenco atleti, lead e switch rapido *AI Attiva / In Pausa*.
- [x] **Guida Utente per il Personal Trainer:** Creazione di `docs/GUIDA_UTENTE_COACH.md` chiara, operativa e pronta da consegnare al coach.

---

## 📚 Documenti e Architettura nel Repo

- 📄 `docs/GUIDA_UTENTE_COACH.md`: Manuale operativo completo e pratico per il Personal Trainer.
- 📄 `docs/SPECIFICATIONS.md`: Specifiche architetturali e funzionali complete.
- 📄 `docs/Proposta_Assistente_AI_Personal_Trainer.pdf`: Proposta commerciale visuale pronta per il PT.
- 📄 `docs/proposta_pt.html`: Sorgente HTML della proposta PT.
- ⚙️ `.github/workflows/ci.yml`: Pipeline di continuous integration multi-versione (3.10, 3.11, 3.12).
- 🧩 Moduli applicativi in `src/coach_flow/`:
  - `domain/`: Entità di dominio, validatori E.164, lifecycle appuntamenti.
  - `calendar/`: Provider modulari (Google Calendar v3 e Mock in-memory).
  - `whatsapp/`: Client ufficiale Meta Cloud API, router webhook, sicurezza HMAC e deterministic button handler.
  - `ai/`: Provider OpenAI / Gemini / Mock, tools di booking e orchestratore `BookingAgent`.
  - `discovery/`: Servizio di outreach con dispatch note vocali per nuovi prospect.
  - `scheduler/`: APScheduler per promemoria T-24h e T-2h anti no-show.
  - `assistant/`: Daily digest mattutino per il PT e alert di emergenza per subentro umano.

---

## 🚀 Istruzioni per Avvio e Testing Locale

### Esecuzione Test e Linter
```bash
source .venv/bin/activate
pytest -v
ruff check .
```

### Avvio Server API
```bash
uvicorn coach_flow.main:app --host 0.0.0.0 --port 8000 --reload
```
Documentazione interattiva OpenAPI disponibile su: `http://localhost:8000/docs`.
