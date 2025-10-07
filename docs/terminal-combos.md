# Combinazioni CLI per l'estrazione dei dati

TruMetraPla apre l'interfaccia grafica quando esegui `trumetrapla` senza argomenti.
Le combinazioni riportate di seguito consentono invece di avviare le modalità a riga
di comando per generare report testuali direttamente dal terminale.

## Avviare la CLI interattiva

```bash
trumetrapla --cli
```

Mostra il menu numerico con cui:
- [1] Generi report Excel guidati
- [2] Compili l'eseguibile Windows (`build-exe`)
- [3] Crei l'installer NSIS (`build-installer`)
- [4] Visualizzi gli script di automazione
- [5] Riapri la GUI da linea di comando

## Report base da file Excel

```bash
trumetrapla report "C:\\Percorso\\produzione.xlsx"
```

Legge il foglio predefinito (indice 0) e stampa il riepilogo di produttività
nel terminale.

## Specificare il foglio di lavoro

```bash
trumetrapla report produzione.xlsx --sheet "Linea 2"
trumetrapla report produzione.xlsx --sheet 3
```

Accetta sia il nome sia l'indice numerico del foglio Excel.

## Mappare manualmente le colonne

Quando le intestazioni non seguono i nomi riconosciuti automaticamente puoi
fornire le corrispondenze.

```bash
trumetrapla report produzione.xlsx \
  --column date "Giorno" \
  --column employee "Operatore" \
  --column process "Reparto" \
  --column machine "Isola" \
  --column process_type "Categoria" \
  --column quantity "Pezzi realizzati" \
  --column duration_minutes "Tempo (min)"
```

Ripeti `--column` per ogni campo canonico. I campi `machine` e `process_type`
sono facoltativi ma puoi indicarli quando vuoi includerli nei report.

## Aggiungere alias permanenti

Gli alias integrativi permettono al riconoscimento automatico di capire nuove
intestazioni senza doverle rimappare ogni volta.

```bash
trumetrapla report produzione.xlsx \
  --alias machine "Centro di lavoro" \
  --alias process_type "Tipo ciclo"
```

Puoi combinare `--alias` con gli altri parametri (`--sheet`, `--column`).

## Eseguire la CLI senza menu interattivo

```bash
trumetrapla --no-interactive
```

Stampa le opzioni principali senza aspettare un input. È utile negli script
quando vuoi ricordare rapidamente i comandi disponibili.

## Altre utilità da terminale

*Generazione eseguibile*
```bash
trumetrapla build-exe --dist dist --onefile
```

*Compilazione installer*
```bash
trumetrapla build-installer --dist dist --reuse-exe
```

Questi comandi possono essere lanciati così come sono oppure tramite il menu
interattivo (`trumetrapla --cli`).
