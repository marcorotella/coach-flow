# Guida Pratica CoachFlow per il Personal Trainer 🏋️‍♂️📱

Benvenuto in **CoachFlow**! Questa guida ti spiega in modo semplice e operativo come funziona il tuo assistente AI su WhatsApp, come gestisce la tua agenda e, soprattutto, come fare in modo che **non fissi mai appuntamenti quando ti alleni o hai impegni personali**.

---

## 🎯 1. Cosa Fa il Tuo Assistente per Te

1. **Accoglie i nuovi contatti (Lead):** risponde subito su WhatsApp, invia un messaggio di benvenuto e la tua vera **nota vocale** registrata.
2. **Fissa gli appuntamenti in autonomia:** dialoga con gli atleti, controlla il tuo calendario in tempo reale e blocca solo gli slot in cui sei realmente disponibile.
3. **Azzera i No-Show:** invia promemoria automatici a 24 ore e a 2 ore dall'appuntamento con pulsanti interattivi (`Confermo ✅`, `Sposta data 🔄`, `Annulla ❌`).
4. **Ti invia il Daily Digest ogni mattina:** ricevi su WhatsApp l'elenco delle sessioni del giorno con lo stato di conferma.
5. **Ti avvisa se serve il tuo intervento (Human Handover):** se l'atleta ha dubbi clinici/infortuni o richieste particolari, il bot ti manda un alert con link diretto per subentrare nella chat.

---

## 🛡️ 2. La Regola d'Oro: Come Evitare Sovrapposizioni con Allenamenti e Impegni Personali

L'assistente è progettato con un **sistema anti-conflitto a 3 livelli**. Ecco come usarlo senza fatica:

```
Livello 1: I tuoi Turni di Lavoro (nella Dashboard Web)
    ⬇
Livello 2: I tuoi Impegni Personali (direttamente dal tuo Google Calendar su smartphone)
    ⬇
Livello 3: Buffer di Riposo (15 minuti automatici tra un cliente e l'altro)
```

### 📱 Dal tuo Smartphone: Il modo più rapido (Google Calendar)
Non devi aprire il computer per bloccare un orario. Se hai un impegno personale, un consulto fuori palestra o la tua sessione di allenamento:
1. Apri la tua consueta app **Google Calendar** (o Apple Calendar collegato) dal tuo smartphone.
2. Crea un evento nell'orario desiderato (es. *"Mio Allenamento"*, *"Visita Medica"*, o *"Consulenza Studio Esterno"*).
3. Assicurati che lo stato dell'evento sia impostato su **"Occupato"** (l'impostazione predefinita di Google Calendar).

> [!IMPORTANT]
> **Il bot interroga il tuo calendario prima di fare qualsiasi proposta su WhatsApp.** Se vede un evento nel tuo calendario personale, quell'orario risulterà occupato e **non verrà mai proposto ad alcun cliente**.

---

### 💻 Dalla Dashboard Web: I tuoi Turni Settimanali
Nella sezione **Orari & Disponibilità** della tua Dashboard puoi impostare la tua settimana tipo con turni spezzati:

*Esempio di configurazione reale:*
- **Lunedì:**
  - Turno Mattina: `07:30 - 12:30`
  - *Pausa Allenamento & Pranzo:* `12:30 - 16:00` (chiusa automaticamente, il bot non accetta prenotazioni)
  - Turno Pomeriggio/Sera: `16:00 - 20:30`
- **Mercoledì:** `08:00 - 14:00` (Pomeriggio libero)
- **Sabato:** `08:30 - 13:00`
- **Domenica:** Spenta / Chiuso

---

### ⏱️ Buffer Automatico di Riposo
Tra una sessione e l'altra (es. sessioni da 60 minuti), CoachFlow inserisce automaticamente un **buffer di sicurezza (es. 15 minuti)**. 
- In questo modo non rischi mai che un atleta arrivi mentre stai ancora finendo con il precedente.
- Hai sempre il tempo di bere, sanificare gli attrezzi o fare la doccia.

---

## 🔔 3. I Messaggi che Ricevi su WhatsApp

### A. Morning Daily Digest (Ogni mattina alle 07:30)
Un messaggio sintetico con la panoramica della tua giornata:
```
Buongiorno Coach! ☀️ Ecco la tua agenda di oggi (Lun 03 Nov):

• 08:30 - Marco Rossi (Confermato ✅)
• 10:00 - Luca Bianchi (In attesa ⏳)
• 17:00 - Giulia Verdi (Confermato ✅)
• 18:30 - Andrea Neri (Confermato ✅)

Totale sessioni: 4
Buon lavoro! 💪
```

### B. Notifica Nuovo Appuntamento Fissato
Ogni volta che un atleta prenota con il bot, ricevi subito un alert:
```
📅 Nuovo appuntamento fissato!
Atleta: Marco Rossi (+39 333 1234567)
Orario: Giovedì 06 Nov, ore 18:00
Durata: 60 min
Evento salvato su Google Calendar.
```

### C. Alert Subentro Umano (Human Handover)
Se il cliente fa domande su ernie, patologie, richieste di sconto o chiede di parlare direttamente con te:
```
⚠️ RICHIESTA DI SUBENTRO UMANO
Atleta: Alessandro Neri (+39 340 9876543)
Motivo: L'atleta segnala dolore acuto al ginocchio e chiede se può fare la prima lezione.

👉 Clicca qui per aprire la chat con l'atleta:
https://wa.me/393409876543
```
Il bot risponderà all'atleta: *"Ho avvisato il Coach, ti risponderà personalmente a breve!"*, mettendosi temporaneamente in pausa su quella conversazione.

---

## 🛠️ 4. Come Usare la Dashboard Web del Coach

Puoi accedere alla Dashboard dal browser del tuo PC o dal telefono su `http://tuo-dominio/dashboard`:

1. **📊 Panoramica:** vedi gli appuntamenti di oggi, i clienti attivi e lo stato delle conferme.
2. **📅 Calendario:** vedi la griglia della settimana; puoi cliccare su **"Aggiungi Blocco / Pausa"** per segnare ferie o blocchi straordinari.
3. **👥 Lead & Atleti:** vedi la scheda di ogni cliente con i suoi obiettivi e note. Con il pulsante **"AI Attiva / In Pausa"** puoi scegliere se gestire un atleta manualmente o lasciarlo al bot.
4. **⚙️ Orari & Regole:** aggiorni in qualsiasi momento i tuoi orari settimanali, la durata delle sedute e i minuti di buffer.

---

## ❓ 5. Domande Frequenti (FAQ)

**Cosa succede se un cliente cancella all'ultimo?**  
Se risponde con il bottone `Annulla ❌` o scrive che non può venire, il bot cancella l'evento da Google Calendar, ti invia una notifica e rimette immediatamente lo slot a disposizione per altri atleti.

**Se mi alleno a orari diversi ogni settimana?**  
Nessun problema: tieni pure gli orari generali impostati nella Dashboard e aggiungi semplicemente il tuo allenamento come evento sul tuo Google Calendar dal telefono. Il bot non si sovrapporrà mai.

**Cosa succede se voglio parlare io con un cliente su WhatsApp?**  
Scrivi direttamente nella chat WhatsApp del cliente dal tuo telefono. Quando il bot rileva che stai intervenendo tu o quando metti in pausa l'AI dalla Dashboard, il bot tace e ti lascia il controllo completo.
