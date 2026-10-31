# CoachFlow - Handover & Session Resume Document 📋

Questo documento serve a trasferire il contesto operativo completo dell'attività da questa sessione locale al server **`ai-terminal`** (sessione **`ai-agy`**).

---

## 📌 Stato del Progetto

- **Nome Progetto:** CoachFlow (`coach-flow`)
- **Repository GitHub:** [https://github.com/marcorotella/coach-flow](https://github.com/marcorotella/coach-flow) (Pubblico, Open Source)
- **Licenza:** MIT
- **Directory di lavoro su `ai-terminal`:** `/home/marco/projects/coach-flow`
- **Ambiente Python:** Python 3.11 con venv in `/home/marco/projects/coach-flow/.venv` (FastAPI, Pydantic, APScheduler, Pytest, Ruff)
- **Stato Test:** 25 test passing (`pytest`), 0 errori di linting (`ruff check .`)
- **CI Pipeline:** Green su GitHub Actions (Python 3.10, 3.11, 3.12)

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

### Milestone 1: `v0.1.0 - Foundation & Modular Calendar Provider` ✅ (100% COMPLETATA)
- [x] **#1:** Project scaffold, CI/CD, linting and base configuration (PR iniziale)
- [x] **#2:** Core domain entities & data models (Trainer, Client, Appointment, Slot) (Chiusa con PR #11)
- [x] **#3:** Modular Calendar Provider abstraction & Google Calendar implementation (Chiusa con PR #12)

### Milestone 2: `v0.2.0 - WhatsApp Cloud API & Deterministic Engine` ✅ (100% COMPLETATA)
- [x] **#4:** Meta WhatsApp Cloud API client & Webhook verification handler (Chiusa con PR #13)
- [x] **#5:** Deterministic interactive button handler (Confirm, Reschedule, Cancel) (Chiusa con PR #14)

### Milestone 3: `v0.3.0 - AI Agent & Conversational Booking` 👈 **PROSSIMA MILESTONE**
- [ ] **#6:** AI Agent Provider abstraction (OpenAI & Gemini support) 👈 **PROSSIMO TASK DA SVILUPPARE**
- [ ] **#7:** AI Tool Calling: check available slots and book appointments
- [ ] **#8:** Voice memo (audio note) dispatch for lead discovery outreach

### Milestone 4: `v0.4.0 - Schedulers & Anti No-Show Automation`
- [ ] **#9:** Background scheduler for interactive T-24h and T-2h reminders
- [ ] **#10:** Trainer Daily Digest agenda and Human Handover emergency alert

---

## 🚀 Prossimo Passo da Eseguire

Lavorare sull'**Issue #6** (Milestone 3):
1. Creare il branch `feature/#6-ai-agent-provider`.
2. Definire l'interfaccia astratta `BaseAIProvider` in `src/coach_flow/ai/base.py` con supporto a system prompt, memory/chat history e tool execution.
3. Implementare il provider Gemini (`GeminiAIProvider`) e/o OpenAI (`OpenAIAgentProvider`).
4. Scrivere i relativi test in `tests/test_ai_provider.py`.
5. Verificare con `pytest` e `ruff check .`.
6. Aprire Pull Request verso `main` per chiudere l'Issue #6.
