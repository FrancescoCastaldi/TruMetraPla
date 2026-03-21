# TruMetraPla

> **Analisi produttività industriale** - Tool desktop e CLI per monitorare dati di produzione da Excel con KPI, dashboard interattiva e report automatizzati.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

---

## Caratteristiche principali

- **Import intelligente** - Riconoscimento automatico colonne Excel (italiano/inglese)
- **Dashboard moderna** - Interfaccia grafica con tema tech minimal e filtri dinamici
- **KPI real-time** - Pezzi prodotti, ore lavorate, produttività media per dipendente/processo
- **Grafici interattivi** - Visualizzazioni a torta per analisi rapide
- **Multi-piattaforma** - Eseguibile Windows + pacchetto Linux
- **CLI completo** - Report da riga di comando con opzioni avanzate 

---

## Installazione

### Requisiti

- Python 3.11 o superiore
- pip (gestore pacchetti Python)

### Metodo 1: Installazione con pip (consigliato)

Installa direttamente dal repository GitHub:

```bash
pip install git+https://github.com/FrancescoCastaldi/TruMetraPla.git
```

### Metodo 2: Installazione da sorgente

Clona il repository e installa in modalità sviluppo:

```bash
# Clona il repository
git clone https://github.com/FrancescoCastaldi/TruMetraPla.git
cd TruMetraPla

# Installa con dipendenze
pip install -e .[test]
```

### Metodo 3: Eseguibile precompilato

**Windows:**
- Scarica `TruMetraPlaSetup.exe` o `TruMetraPla.exe` dalla sezione [Releases](https://github.com/FrancescoCastaldi/TruMetraPla/releases)
- Esegui l'installer o l'eseguibile portatile
- Nessuna installazione Python necessaria

**Linux:**
- Scarica `trumetrapla-*.tar.gz` dalla sezione [Releases](https://github.com/FrancescoCastaldi/TruMetraPla/releases)
- Estrai ed esegui lo script di installazione:

```bash
tar xzf trumetrapla-*.tar.gz
cd trumetrapla-*/
sudo ./install.sh
```

### Verifica installazione

Dopo l'installazione, verifica che tutto funzioni:

```bash
# Mostra versione e aiuto
trumetrapla --help

# Avvia la dashboard
trumetrapla
```

## Quick start

### Installazione

```bash
pip install -e .[test]
```

### Utilizzo base

```bash
# Apri la dashboard interattiva
trumetrapla

# Genera report da CLI
trumetrapla report produzione.xlsx

# Crea pacchetto Linux
trumetrapla build-linux
```

---

## Dashboard desktop

La GUI offre un'esperienza completa per l'analisi dei dati:

- **Caricamento file** - Drag & drop o menu File → Apri
- **Filtri dinamici** - Filtra per operatore, processo, macchina
- **Tabella interattiva** - Visualizza tutti i KPI con colonne ordinabili
- **Grafici** - Report a torta basati su processo/operatore
- **Export** - Salva dati filtrati in CSV

### Avvio dashboard

**Da codice:**

```bash
trumetrapla
```

**Da eseguibile Windows:**

- Doppio click su `dist/TruMetraPla.exe`
- Oppure installa con l'installer automatico

---

## Build & distribuzione

### Eseguibile Windows (.exe)

```bash
# Genera con PyInstaller
pyinstaller TruMetraPla.spec

# Eseguibile disponibile in dist/
```

### Pacchetto Linux (.tar.gz)

```bash
# Build automatico
trumetrapla build-linux

# Output: dist/trumetrapla-*.tar.gz
```

**Installazione su Linux:**

```bash
tar xzf trumetrapla-*.tar.gz
cd trumetrapla-*/
./install.sh
```

---

## CLI

### Report completo

```bash
trumetrapla report produzione.xlsx
```

### Opzioni avanzate

```bash
# Filtra per operatore
trumetrapla report produzione.xlsx --operatore "Mario Rossi"

# Filtra per processo
trumetrapla report produzione.xlsx --processo "Assemblaggio"

# Esporta in JSON
trumetrapla report produzione.xlsx --format json > output.json

# Salva su file
trumetrapla report produzione.xlsx > report.txt
```

---

## Uso come libreria

```python
from trumetrapla import load_data, calculate_metrics

# Carica dati
operations = load_data("produzione.xlsx")

# Calcola KPI
metrics = calculate_metrics(operations)

print(f"Pezzi totali: {metrics.total_pieces}")
print(f"Ore lavorate: {metrics.total_hours}")
print(f"Produttività media: {metrics.avg_productivity:.2f} pz/h")
```

---

## Requisiti di sistema

- **Python:** 3.11+
- **Dipendenze:** pandas, openpyxl, tkinter, ttkbootstrap
- **Sistema operativo:** Windows 10+, Linux (Ubuntu 20.04+, Debian 11+)
- **RAM consigliata:** 2 GB minimo, 4 GB per file Excel di grandi dimensioni
- **Risoluzione schermo:** Minimo 1280x720 per una visualizzazione ottimale della dashboard

---

## Mappatura colonne

TruMetraPla riconosce automaticamente le seguenti colonne Excel:

| Italiano | English | Tipo |
|----------|---------|------|
| Data / Giorno | Date / Day | Data |
| Operatore / Dipendente | Operator / Employee | Testo |
| Processo / Reparto | Process / Department | Testo |
| Macchina / Attrezzatura | Machine / Equipment | Testo |
| Pezzi / Quantità | Pieces / Quantity | Numero |
| Ore / Tempo | Hours / Time | Numero |

**Nota:** Il sistema supporta colonne extra non mappate (vengono conservate nei dati ma non utilizzate per i KPI).

---

## Sviluppo

### Setup ambiente

```bash
git clone https://github.com/FrancescoCastaldi/TruMetraPla.git
cd TruMetraPla
pip install -e .[test]
```

### Test

```bash
pytest tests/
```

### Struttura progetto

```
TruMetraPla/
├── src/trumetrapla/
│   ├── __main__.py      # Entry point CLI
│   ├── data_loader.py   # Import Excel
│   ├── gui.py           # Dashboard Tkinter
│   ├── metrics.py       # Calcolo KPI
│   └── models.py        # Data models
├── tests/               # Test suite
└── docs/                # Documentazione
```

---

## Installazione Windows

### Opzione 1: Installer automatico

1. Scarica `TruMetraPlaSetup.exe` dalla sezione [Releases](https://github.com/FrancescoCastaldi/TruMetraPla/releases)
2. Esegui l'installer e segui le istruzioni
3. Avvia TruMetraPla dal menu Start

### Opzione 2: Eseguibile portatile

1. Scarica `TruMetraPla.exe` standalone
2. Esegui direttamente (nessuna installazione necessaria)

---

## Installazione Linux

### Ubuntu/Debian

```bash
wget https://github.com/FrancescoCastaldi/TruMetraPla/releases/latest/download/trumetrapla-latest.tar.gz
tar xzf trumetrapla-latest.tar.gz
cd trumetrapla-*/
sudo ./install.sh
```

### Arch/Manjaro

```bash
# Installa da AUR (quando disponibile)
yay -S trumetrapla
```

---

## FAQ

**Q: Come esporto i dati filtrati?**

A: Nella dashboard grafica, applica i filtri desiderati e clicca su "Esporta CSV".

**Q: Dove vengono salvati i report?**

A: I report CLI vengono stampati a schermo. Usa `> output.txt` per salvarli su file.

**Q: Il file Excel ha colonne in inglese, funziona?**

A: Sì, il sistema riconosce automaticamente sia nomi italiani che inglesi.

**Q: Posso usare il programma senza installare Python?**

A: Sì, usa l'eseguibile Windows (.exe) o il pacchetto Linux precompilato.

---

## Link utili

- [Documentazione completa](docs/)
- [Issue tracker](https://github.com/FrancescoCastaldi/TruMetraPla/issues)
- [Wiki](https://github.com/FrancescoCastaldi/TruMetraPla/wiki)

---

## Licenza

MIT License - Vedi [LICENSE](LICENSE) per dettagli.

---

## Novità recenti

### v2.0 (Work in Progress)

- Nuovo tema UI "Tech Minimal" - Design pulito e professionale
- Grafici a barre interattivi
- Export CSV integrato
- Supporto colonne Excel arbitrarie
- Performance migliorate nel caricamento dati

---

<p align="center">
  <i>Sviluppato con Python per l'analisi della produttività industriale</i>
</p>
