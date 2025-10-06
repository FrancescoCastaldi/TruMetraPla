# TruMetraPla

TruMetraPla monitora la produttività nei processi metalmeccanici importando dati da file Excel e offrendo strumenti per analizzare KPI, grafici e performance di dipendenti e processi.

## Funzionalità principali

- Import automatico di file Excel con riconoscimento delle intestazioni italiane e inglesi.
- Calcolo dei principali indicatori: pezzi prodotti, ore lavorate, produttività media.
- Aggregazioni per dipendente, processo e giorno con ordinamento per produttività.
- Consolle grafica moderna con menu a tendina, filtri, tabella interattiva e grafico a torta per analizzare i file Excel.
- Eseguibile Windows che apre una dashboard desktop con caricamento file guidato e riepiloghi KPI.

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

### Avvio da riga di comando

Dopo l'installazione è disponibile il comando `trumetrapla`. Se avviato senza argomenti mostra l'interfaccia di benvenuto testuale che permette di:

1. Generare un report guidato a partire da un file Excel.
2. Visualizzare le istruzioni per creare l'eseguibile e l'installer Windows.

Per limitarsi alla sola stampa del menu senza interazione puoi usare:

```bash
trumetrapla --no-interactive
```

### Avvio dall'eseguibile Windows

Il file `TruMetraPla.exe` generato con PyInstaller (o installato tramite l'installer automatico) apre una dashboard desktop pensata per l'analisi rapida dei dati.
La schermata principale offre:

- **Menu File** con la voce *Apri file Excel…* per selezionare il file da importare.
- **Filtri a tendina** per isolare rapidamente un singolo dipendente o processo produttivo.
- **Tabella interattiva** con le colonne normalizzate (data, dipendente, processo, pezzi, durata e produttività oraria).
- **Pulsanti "Mostra KPI" e "Grafico a torta"** per aprire rispettivamente il riepilogo numerico e la distribuzione visiva dei pezzi prodotti.

Al caricamento viene aggiornato lo stato nella barra inferiore, insieme al riepilogo dei totali (pezzi, ore, throughput e numero di dipendenti/processi). In assenza del runtime grafico Windows, l'applicazione ripiega automaticamente sulla CLI.

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
2. Genera l'eseguibile lanciando `trumetrapla build-exe`, utilizzando il menu interattivo, lo script PowerShell **oppure il nuovo file batch** `installer/Build-TruMetraPla.bat`. Verrà creato `TruMetraPla.exe` nella cartella `dist/`; facendo doppio clic sull'eseguibile si aprirà direttamente la finestra grafica di benvenuto.
3. (Opzionale ma consigliato) Compila l'installer grafico con `trumetrapla build-installer`. Il comando crea `TruMetraPla_Setup_<versione>.exe` pronto per l'utente finale.

### Creare l'installer automatico

Per produrre un file `TruMetraPla_Setup.exe` che installi automaticamente il programma in `C:\TruMetraPla`:

```powershell
pip install .[build]
trumetrapla build-installer
```

Il comando verifica la presenza di NSIS (`makensis`) e, se necessario, genera prima l'eseguibile stand-alone. Il risultato viene salvato nella cartella `dist/` e può essere distribuito direttamente: facendo doppio clic sull'installer viene avviata una procedura guidata che copia i file nella cartella predefinita, crea le scorciatoie sul desktop e nel menu Start e apre la finestra di benvenuto al termine dell'installazione.

Per personalizzare la cartella di output:

```powershell
trumetrapla build-installer --dist C:\Percorso\Personalizzato
```

Se desideri rigenerare da zero anche l'eseguibile (ignorando eventuali build precedenti) aggiungi `--no-reuse-exe`.

### Dove viene installato il software

- **Eseguibile portabile**: il comando `trumetrapla build-exe` e lo script `Setup-TruMetraPla.ps1` copiano l'eseguibile nella cartella di destinazione (`dist/` per impostazione predefinita). Il parametro `-Output` dello script PowerShell permette di scegliere una directory diversa.
- **Installer automatico**: il comando `trumetrapla build-installer` utilizza lo script `TruMetraPla-Installer.nsi` per creare `TruMetraPla_Setup_<versione>.exe`, che installa l'applicazione in `C:\TruMetraPla` (variabile `INSTALL_DIR`). Puoi modificare questo percorso aprendo lo script con un editor di testo e cambiando la variabile, oppure l'utente finale può selezionare una cartella differente nella schermata "Cartella di installazione".

### Automazione da PowerShell

Per Windows sono disponibili gli script `installer/Setup-TruMetraPla.ps1` (PowerShell) e `installer/Build-TruMetraPla.bat` (Prompt dei comandi) che:

- crea o aggiorna un ambiente virtuale dedicato;
- installa il progetto con le dipendenze necessarie alla build;
- invocano `trumetrapla build-exe` con la cartella di destinazione desiderata;
- opzionalmente compila l'installer grafico NSIS (parametro `-IncludeInstaller`, che usa `trumetrapla build-installer`).

Esempio di utilizzo completo:

```powershell
powershell -ExecutionPolicy Bypass -File installer/Setup-TruMetraPla.ps1 -IncludeInstaller
```

```bat
installer\Build-TruMetraPla.bat --dist C:\Percorso\Output
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
