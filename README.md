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

## 📚 Documentazione di Progetto

- [Specifiche Funzionali e Tecniche Complete](docs/SPECIFICATIONS.md)
- [Proposta Esecutiva Personal Trainer (PDF)](docs/Proposta_Assistente_AI_Personal_Trainer.pdf)

---

## 🤝 Contribuzione

I contributi sono benvenuti! Leggi la [Guida alla Contribuzione (CONTRIBUTING.md)](CONTRIBUTING.md) per scoprire come aprire Issue, inviare Pull Request e rispettare gli standard del codice.

---

## ⚖️ Licenza

Questo progetto è distribuito sotto licenza **MIT**. Consulta il file [LICENSE](LICENSE) per i dettagli.
