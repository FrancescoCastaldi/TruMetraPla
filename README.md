# TruMetraPla

TruMetraPla è uno strumento desktop/CLI per analizzare rapidamente dati di produzione provenienti da Excel, generare KPI e costruire eseguibili Windows pronti per l'uso in officina.

## Avvio rapido
- **Installazione locale**: `pip install -e .[test]`
- **Dashboard desktop**: `trumetrapla` oppure esegui `dist/TruMetraPla.exe`
- **Report CLI immediato**: `trumetrapla report produzione.xlsx`

## Importazione dei file Excel
- Riconoscimento automatico delle intestazioni in italiano/inglese.
- In caso di colonne sconosciute, viene mostrata una finestra per associare manualmente i campi richiesti (data, dipendente, processo, quantità, minuti).
- Supporto per alias personalizzati dalla CLI: `trumetrapla report file.xlsx --column quantity "Pezzi prodotti"`.

## Dashboard e grafici
- Filtri rapidi per dipendente/processo, tabella interattiva e riepilogo KPI.
- Finestra dedicata ai grafici a torta per confrontare produttività per processo o operatore.

## Automazione Windows
- `installer/Setup-TruMetraPla.ps1` prepara l'ambiente e genera eseguibile e installer.
- `installer/Build-TruMetraPla.bat` esegue la stessa procedura da Prompt dei comandi con doppio clic.

## Gestione dei conflitti su GitHub
1. Apri la Pull Request e premi **Resolve conflicts**.
2. Nella vista di modifica elimina i marcatori `<<<<<<<`, `=======` e `>>>>>>>`, scegliendo solo le righe da mantenere.
3. Verifica che il file risultante sia valido (puoi usare **Preview** o scaricarlo e provarlo in locale).
4. Quando il conflitto è risolto, clicca **Mark as resolved** e poi **Commit merge** per salvare.

In alternativa, puoi risolvere i conflitti in locale:
1. Esegui `git fetch` e `git merge origin/main` (o il branch in conflitto).
2. Modifica manualmente i file rimuovendo i marcatori di conflitto.
3. Lancia i test, quindi usa `git add` sui file corretti e `git commit`.
4. Spingi le modifiche con `git push` per aggiornare la Pull Request.
