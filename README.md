# TruMetraPla

Strumento desktop e CLI per analizzare dati di produzione da Excel, calcolare KPI e distribuire rapidamente report o eseguibili Windows.

## Utilizzo rapido
- **Installazione**: `pip install -e .[test]`
- **Dashboard**: `trumetrapla` (oppure avvia `dist/TruMetraPla.exe` dopo il build)
- **Report CLI**: `trumetrapla report produzione.xlsx`

## Gestione dei file Excel
- Rilevamento automatico di intestazioni italiane/inglesi.
- Dialog di mappatura per associare manualmente data, dipendente, processo, quantità e minuti quando necessario.
- Alias opzionali dalla CLI: `trumetrapla report file.xlsx --column quantity "Pezzi prodotti"`.

## Dashboard
- Filtri per operatore/processo e tabella con KPI.
- Finestra grafica con report a torta basati su processo o operatore.

## Automazione Windows
- `installer/Setup-TruMetraPla.ps1` crea l'ambiente e genera l'eseguibile.
- `installer/Build-TruMetraPla.bat` offre la stessa procedura tramite doppio clic.
