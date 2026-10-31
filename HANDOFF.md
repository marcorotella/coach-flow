# CoachFlow - Handover & Session Resume Document 📋

Questo documento serve a trasferire il contesto operativo completo dell'attività da questa sessione locale al server **`ai-terminal`** (sessione **`ai-agy`**).

---

## 📌 Stato del Progetto

- **Nome Progetto:** CoachFlow (`coach-flow`)
- **Repository GitHub:** [https://github.com/marcorotella/coach-flow](https://github.com/marcorotella/coach-flow) (Pubblico, Open Source)
- **Licenza:** MIT
- **Directory di lavoro su `ai-terminal`:** `/home/marco/projects/coach-flow`
- **Ambiente Python:** Python 3.11 con venv in `/home/marco/projects/coach-flow/.venv` (FastAPI, Pydantic, APScheduler, Pytest, Ruff)
- **Stato Test:** 2 test passing (`pytest`)

---

## 🎯 Obiettivi e Flussi di CoachFlow

Assistente AI su WhatsApp per Personal Trainer:
1. **Discovery & Primo Contatto:** Invio primo messaggio WhatsApp + **nota vocale registrata dal coach** (formato audio nativo WhatsApp OGG/Opus).
2. **Booking Conversazionale:** Negoziazione slot con AI, lettura/scrittura su **Google Calendar** (architettura modulare `BaseCalendarProvider`).
3. **Anti No-Show (Costo Zero-LLM):** Promemoria interattivi a T-24h e T-2h con pulsanti (`Confermo ✅`, `Sposta 🔄`, `Annulla ❌`). Intercettati a livello deterministico senza sprecare token AI.
4. **Trainer Assistant:** Daily Digest mattutino per il PT su WhatsApp e notifica di emergenza per subentro umano.

---

## 📚 Documenti Chiave nel Repo

- 📄 `docs/SPECIFICATIONS.md`: Specifiche architetturali e funzionali complete.
- 📄 `docs/Proposta_Assistente_AI_Personal_Trainer.pdf`: Documento visuale di 2 pagine pronto da inviare al Personal Trainer.
- 📄 `docs/proposta_pt.html`: Sorgente HTML utilizzato per generare il PDF.
- ⚙️ `.github/workflows/ci.yml`: Pipeline di CI per test e linting automatico su Python 3.10, 3.11, 3.12.

---

## 📋 Milestones e Issues su GitHub

Tutte le milestone e le issue sono già create su GitHub:

### Milestone 1: `v0.1.0 - Foundation & Modular Calendar Provider`
- [x] **#1:** Project scaffold, CI/CD, linting and base configuration (Completata con PR/commit iniziale)
- [ ] **#2:** Core domain entities & data models (Trainer, Client, Appointment, Slot) 👈 **PROSSIMO TASK DA SVILUPPARE**
- [ ] **#3:** Modular Calendar Provider abstraction & Google Calendar implementation

### Milestone 2: `v0.2.0 - WhatsApp Cloud API & Deterministic Engine`
- [ ] **#4:** Meta WhatsApp Cloud API client & Webhook verification handler
- [ ] **#5:** Deterministic interactive button handler (Confirm, Reschedule, Cancel)

### Milestone 3: `v0.3.0 - AI Agent & Conversational Booking`
- [ ] **#6:** AI Agent Provider abstraction (OpenAI & Gemini support)
- [ ] **#7:** AI Tool Calling: check available slots and book appointments
- [ ] **#8:** Voice memo (audio note) dispatch for lead discovery outreach

### Milestone 4: `v0.4.0 - Schedulers & Anti No-Show Automation`
- [ ] **#9:** Background scheduler for interactive T-24h and T-2h reminders
- [ ] **#10:** Trainer Daily Digest agenda and Human Handover emergency alert

---

## 🚀 Prossimo Passo da Eseguire nella Nuova Sessione

Lavorare sull'**Issue #2**:
1. Creare il branch `feature/#2-core-domain-models`.
2. Definire i modelli Pydantic in `src/coach_flow/domain/`:
   - `Trainer` (id, name, phone, availability_window, session_duration_minutes)
   - `Client` / `Lead` (id, name, phone, notes, status: lead | active | paused)
   - `TimeSlot` (start_time, end_time, is_available)
   - `Appointment` (id, trainer_id, client_id, start_time, end_time, status: scheduled | confirmed | rescheduled | cancelled)
3. Scrivere i relativi test in `tests/test_domain_models.py`.
4. Eseguire `pytest` e `ruff check .`.
5. Aprire Pull Request verso `main` per chiudere l'Issue #2.
