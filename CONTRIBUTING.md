# Guida alla Contribuzione di CoachFlow 🚀

Grazie per il tuo interesse nel contribuire a **CoachFlow**! Questo è un progetto open-source dedicato ad aiutare i Personal Trainer e i professionisti del fitness ad automatizzare e migliorare la gestione dei propri appuntamenti tramite WhatsApp e intelligenza artificiale.

## 🌿 Flusso di Lavoro Git

1. **Trova o apri una Issue:** Ogni sviluppo deve essere tracciato da una Issue di riferimento.
2. **Crea un Branch dedicato:** Usa il formato:
   - `feature/#<id>-nome-breve`
   - `fix/#<id>-nome-breve`
3. **Sviluppa e testa localmente:**
   ```bash
   pip install -e ".[dev]"
   ruff check .
   pytest
   ```
4. **Apri una Pull Request:**
   - Collega la Issue nella descrizione (es. `Closes #1`).
   - Assicurati che i controlli CI di GitHub Actions siano verdi.
   - Attendi la revisione prima del merge su `main`.

## 📜 Convenzione dei Commit (Conventional Commits)
- `feat:` nuove funzionalità
- `fix:` correzione di bug
- `docs:` modifiche alla documentazione
- `refactor:` refactoring del codice senza modifiche di comportamento
- `test:` aggiunta o modifica di test

## ⚖️ Licenza
Inviando contributi a questo repository, accetti che il tuo codice venga distribuito sotto licenza **MIT**.
