# 📊 TruMetraPla

> **Analisi produttività industriale** - Tool desktop e CLI per monitorare dati di produzione da Excel con KPI, dashboard interattiva e report automatizzati.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

---

## ✨ Caratteristiche Principali

✅ **Import Intelligente** - Riconoscimento automatico colonne Excel (italiano/inglese)  
✅ **Dashboard Moderna** - Interfaccia grafica con tema tech minimal e filtri dinamici  
✅ **KPI Real-time** - Pezzi prodotti, ore lavorate, produttività media per dipendente/processo  
✅ **Grafici Interattivi** - Visualizzazioni a torta per analisi rapide  
✅ **Multi-piattaforma** - Eseguibile Windows + pacchetto Linux  
✅ **CLI Completo** - Report da riga di comando con opzioni avanzate  

---

## 🚀 Quick Start

### Installazione

```bash
pip install -e .[test]
```

### Utilizzo Base

```bash
# Apri la dashboard interattiva
trumetrapla

# Genera report da CLI
trumetrapla report produzione.xlsx

# Crea pacchetto Linux
trumetrapla build-linux
```

---

## 💻 Dashboard Desktop

La GUI offre un'esperienza completa per l'analisi dei dati:

- **📁 Caricamento File** - Drag & drop o menu File → Apri
- **🎯 Filtri Dinamici** - Filtra per operatore, processo, macchina
- **📊 Tabella Interattiva** - Visualizza tutti i KPI con colonne ordinabili
- **📊 Grafici** - Report a torta basati su processo/operatore
- **💾 Export** - Salva dati filtrati in CSV

### Avvio Dashboard

**Da codice:**
```bash
trumetrapla
```

**Da eseguibile Windows:**
- Doppio click su `dist/TruMetraPla.exe`
- Oppure installa con l'installer automatico

---

## 🛠️ Build & Distribuzione

### Windows

#### Metodo 1: Build Automatico
```batch
installer\Setup-TruMetraPla.bat
installer\Build-TruMetraPla.bat --include-installer
```

#### Metodo 2: Manuale
```bash
pip install .[build]
trumetrapla build-exe
trumetrapla build-installer
```

**Output:**
- `dist/TruMetraPla.exe` - Eseguibile stand-alone
- `dist/TruMetraPla_Setup.exe` - Installer NSIS

### Linux (Ubuntu/Xubuntu)

```bash
pip install .[build]
trumetrapla build-linux
```

**Installazione:**
```bash
tar -xf dist/TruMetraPla-linux.tar.gz
cd TruMetraPla-linux
sudo ./install.sh
```

Installa in `/opt/trumetrapla` e crea link in `/usr/local/bin`.

---

## 📜 Interfaccia CLI

### Report Base
```bash
trumetrapla report produzione.xlsx
```

### Opzioni Avanzate
```bash
# Specifica foglio Excel
trumetrapla report produzione.xlsx --sheet "Dati 2026"

# Mappatura colonne personalizzata
trumetrapla report produzione.xlsx \
  --column quantity "Pezzi prodotti" \
  --column employee "Nome operatore"

# Alias personalizzati
trumetrapla report produzione.xlsx \
  --alias employee "Operatore,Worker"
```

### Parametri Disponibili

| Opzione | Descrizione | Esempio |
|---------|-------------|----------|
| `--sheet` | Nome o indice foglio Excel | `--sheet 0` o `--sheet "Gennaio"` |
| `--column` | Mappa campo → colonna | `--column date "Data produzione"` |
| `--alias` | Alias per riconoscimento automatico | `--alias quantity "Pezzi,Pcs"` |

---

## 📚 Uso come Libreria Python

```python
from pathlib import Path
from trumetrapla import (
    load_operations_from_excel,
    summarize_operations,
    group_by_employee,
    group_by_process,
    daily_trend,
)

# Carica dati
records = load_operations_from_excel(Path("produzione.xlsx"))

# Statistiche generali
summary = summarize_operations(records)
print(f"Totale pezzi: {summary.total_quantity}")
print(f"Throughput medio: {summary.throughput:.2f} pz/ora")

# Raggruppa per dipendente
top_employees = group_by_employee(records)[:5]
for emp in top_employees:
    print(f"{emp.entity}: {emp.total_quantity} pezzi")

# Trend giornaliero
trend = daily_trend(records)
for day in trend:
    print(f"{day.date}: {day.total_quantity} pezzi")
```

---

## ⚙️ Requisiti di Sistema

### Windows
- Windows 10/11 (64-bit)
- Python 3.11+
- Visual C++ Build Tools (per PyInstaller)
- NSIS (opzionale, per installer grafico)

### Linux
- Ubuntu 22.04+ o derivati (Xubuntu, etc.)
- Python 3.11+
- `python3-venv`, `desktop-file-utils`

---

## 📝 Mappatura Colonne Excel

### Campi Richiesti
- **date** - Data produzione
- **employee** - Dipendente/Operatore
- **process** - Processo/Fase lavorazione
- **quantity** - Pezzi prodotti
- **duration_minutes** - Durata in minuti

### Campi Opzionali
- **machine** - Macchina utilizzata
- **process_type** - Tipologia processo
- **Extra** - Qualsiasi altra colonna viene importata automaticamente

### Riconoscimento Automatico

TruMetraPla riconosce automaticamente intestazioni comuni in italiano e inglese:

| Campo | Alias riconosciuti |
|-------|--------------------|
| date | data, date, giorno |
| employee | dipendente, operatore, employee, worker |
| process | processo, fase, linea, process, activity |
| quantity | quantità, pezzi, quantity, pieces |
| duration_minutes | durata, minuti, minutes, tempo |

---

## 🔧 Sviluppo

### Setup Ambiente Dev
```bash
git clone https://github.com/FrancescoCastaldi/TruMetraPla.git
cd TruMetraPla
pip install -e .[test]
```

### Run Tests
```bash
pytest
```

### Struttura Progetto
```
TruMetraPla/
├── src/trumetrapla/
│   ├── cli.py              # Interfaccia CLI
│   ├── gui.py              # Dashboard grafica
│   ├── data_loader.py      # Import Excel
│   ├── metrics.py          # Calcolo KPI
│   └── models.py           # Modelli dati
├── installer/           # Script build Windows/Linux
├── tests/               # Unit tests
└── docs/                # Documentazione
```

---

## 📦 Installazione Completa Windows

### Opzione A: Installer Automatico (Consigliato)
1. Scarica `TruMetraPla_Setup.exe`
2. Esegui l'installer
3. Segui la procedura guidata
4. Lancia da menu Start o icona desktop

### Opzione B: Build da Codice
```batch
# Setup ambiente e dipendenze
installer\Setup-TruMetraPla.bat

# Build eseguibile + installer
installer\Build-TruMetraPla.bat --include-installer

# L'installer sarà in dist/TruMetraPla_Setup.exe
```

**Cartella di installazione:** `C:\TruMetraPla` (modificabile durante setup)

---

## 🐧 Installazione Linux

### Metodo Automatico (Xubuntu/Ubuntu)
```bash
cd installer
./install-trumetrapla-xubuntu.sh
```

### Metodo Manuale
```bash
# Build pacchetto
pip install .[build]
trumetrapla build-linux

# Estrai e installa
tar -xf dist/TruMetraPla-linux.tar.gz
cd TruMetraPla-linux
sudo ./install.sh
```

### Personalizzazione Path
Modifica `PREFIX` e `BIN_DEST` in `install.sh` prima dell'esecuzione.

---

## 💬 FAQ

**Q: Come faccio se Excel ha colonne con nomi diversi?**  
A: Usa l'opzione `--column` per mappare manualmente, oppure `--alias` per aggiungere alias riconosciuti automaticamente.

**Q: Posso usare TruMetraPla su macOS?**  
A: Attualmente supportato solo Windows e Linux. Il codice Python funziona su macOS ma non è disponibile il pacchetto pre-compilato.

**Q: Come esporto i dati filtrati?**  
A: Nella dashboard grafica, applica i filtri desiderati e clicca su "Esporta CSV".

**Q: Dove vengono salvati i report?**  
A: I report CLI vengono stampati a schermo. Usa `> output.txt` per salvarli su file.

---

## 🔗 Link Utili

- [Documentazione Completa](docs/)
- [Issue Tracker](https://github.com/FrancescoCastaldi/TruMetraPla/issues)
- [Wiki](https://github.com/FrancescoCastaldi/TruMetraPla/wiki)

---

## 📜 Licenza

MIT License - Vedi [LICENSE](LICENSE) per dettagli.

---

## ✨ Novità Recenti

### v2.0 (Work in Progress)
- 🎨 Nuovo tema UI "Tech Minimal" - Design pulito e professionale
- 📊 Grafici a barre interattivi
- 💾 Export CSV integrato
- 🔧 Supporto colonne Excel arbitrarie
- ⚡ Performance migliorate nel caricamento dati

---

<p align="center">
  <sub>Sviluppato con ❤️ da <a href="https://github.com/FrancescoCastaldi">Francesco Castaldi</a></sub>
</p>
