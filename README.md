# TruMetraPla

TruMetraPla monitora la produttività nei processi metalmeccanici importando dati da file Excel e offrendo strumenti per analizzare KPI, grafici e performance di dipendenti e processi.

## Funzionalità principali

- Import automatico di file Excel con riconoscimento delle intestazioni italiane e inglesi.
- Calcolo dei principali indicatori: pezzi prodotti, ore lavorate, produttività media.
- Aggregazioni per dipendente, processo e giorno con ordinamento per produttività.
- Interfaccia di benvenuto interattiva con guida alla creazione dell'eseguibile Windows.

## Installazione

Il progetto utilizza Python 3.11+. Per installare le dipendenze in modalità sviluppo è sufficiente eseguire:

```bash
pip install -e .[test]
```

### Requisiti per l'installazione su Windows

Per creare ed eseguire l'installer Windows assicurati di avere a disposizione:

1. **Sistema operativo**: Windows 10 o Windows 11 a 64 bit con tutti gli aggiornamenti recenti.
2. **Python**: versione 3.11 o superiore installata dal [Microsoft Store](https://www.microsoft.com/store/productId/9PJPW5LDXLZ5) oppure dal sito ufficiale, con l'opzione "Aggiungi Python al PATH" abilitata.
3. **PowerShell**: versione 5.1 o PowerShell 7+ per poter eseguire lo script `installer/Setup-TruMetraPla.ps1`.
4. **Strumenti di compilazione**: Microsoft Visual C++ Build Tools o un'installazione recente di Visual Studio con il carico di lavoro "Sviluppo desktop con C++" per garantire la disponibilità dei compilatori necessari a PyInstaller.
5. **Dipendenze Python**: pacchetti elencati nell'extra `build` (`pip install .[build]`), che includono PyInstaller.
6. **NSIS (opzionale)**: se desideri generare anche l'installer grafico, installa [Nullsoft Scriptable Install System](https://nsis.sourceforge.io/Download).

Tutti i requisiti vengono gestiti automaticamente dallo script PowerShell, che verifica la presenza di Python e, se necessario, crea l'ambiente virtuale e installa le dipendenze.

## Interfaccia di benvenuto

Dopo l'installazione è disponibile il comando `trumetrapla`. Se avviato senza argomenti mostra l'interfaccia di benvenuto che permette di:

1. Generare un report guidato a partire da un file Excel.
2. Visualizzare le istruzioni per creare l'eseguibile e l'installer Windows.

Per limitarsi alla sola stampa del menu senza interazione puoi usare:

```bash
trumetrapla --no-interactive
```

## Interfaccia a riga di comando (modalità diretta)

Per generare un report direttamente da riga di comando:

```bash
trumetrapla report produzione.xlsx
```

Opzioni principali:

- `--sheet`: nome o indice del foglio Excel da analizzare.
- `--column`: associazione esplicita tra un campo canonico (`date`, `employee`, `process`, `quantity`, `duration_minutes`) e la colonna nel file.
- `--alias`: aggiunge alias personalizzati per l'autoricnoscimento delle colonne.

Esempio di mappatura personalizzata:

```bash
trumetrapla report produzione.xlsx --column quantity "Pezzi prodotti" --alias employee Operatore
```

## Costruire l'eseguibile Windows

1. Installa le dipendenze di build: `pip install .[build]` (su Windows con Python 3.11 o superiore) oppure esegui lo script `powershell -ExecutionPolicy Bypass -File installer/Setup-TruMetraPla.ps1`.
2. Genera l'eseguibile lanciando `trumetrapla build-exe`, utilizzando il menu interattivo oppure affidandoti allo script PowerShell. Verrà creato `TruMetraPla.exe` nella cartella `dist/`.
3. (Opzionale) Crea un installer grafico con [NSIS](https://nsis.sourceforge.io/). Apri `installer/TruMetraPla-Installer.nsi`, aggiorna eventuali percorsi/versioni e compila lo script per ottenere `TruMetraPla_Setup_0.1.0.exe`.

### Dove viene installato il software

- **Eseguibile portabile**: il comando `trumetrapla build-exe` e lo script `Setup-TruMetraPla.ps1` copiano l'eseguibile nella cartella di destinazione (`dist/` per impostazione predefinita). Il parametro `-Output` dello script PowerShell permette di scegliere una directory diversa.
- **Installer NSIS**: lo script `TruMetraPla-Installer.nsi` installa l'applicazione in `C:\Program Files\TruMetraPla` (variabile `INSTALL_DIR`). Puoi modificare questo percorso aprendo lo script con un editor di testo e cambiando la variabile, oppure l'utente finale può selezionare una cartella differente nella prima schermata dell'installer.

### Automazione da PowerShell

Per Windows è disponibile lo script `installer/Setup-TruMetraPla.ps1` che:

- crea o aggiorna un ambiente virtuale dedicato;
- installa il progetto con le dipendenze necessarie alla build;
- invoca `trumetrapla build-exe` con la cartella di destinazione desiderata;
- opzionalmente compila l'installer grafico NSIS (parametro `-IncludeInstaller`).

Esempio di utilizzo completo:

```powershell
powershell -ExecutionPolicy Bypass -File installer/Setup-TruMetraPla.ps1 -IncludeInstaller
```

## Utilizzo come libreria Python

```python
from pathlib import Path
from trumetrapla import (
    daily_trend,
    group_by_employee,
    load_operations_from_excel,
    summarize_operations,
)

records = load_operations_from_excel(Path("produzione.xlsx"))
summary = summarize_operations(records)
print(summary.total_quantity)
```

## Branch di sincronizzazione

Per evitare l'errore `fatal: couldn't find remote ref PSite` durante le operazioni automatiche di fetch, il repository include un workflow GitHub Actions che mantiene aggiornato il branch `PSite` sincronizzandolo con l'ultimo commit dei branch principali (`work`, `main` o `master`). In questo modo gli script esterni che fanno riferimento a `PSite` troveranno sempre la relativa ref remota.
