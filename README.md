# TruMetraPla

TruMetraPla monitora la produttività nei processi metalmeccanici, importando dati da file Excel e offrendo strumenti per analizzare KPI, grafici e performance di dipendenti e processi.

## Funzionalità principali

- Import automatico di file Excel con riconoscimento delle intestazioni italiane e inglesi.
- Calcolo dei principali indicatori: pezzi prodotti, ore lavorate, produttività media.
- Aggregazioni per dipendente, processo e giorno con ordinamento per produttività.
- Interfaccia a riga di comando per ottenere rapidamente un riepilogo operativo.

## Installazione

Il progetto utilizza Python 3.11+. Per installare le dipendenze in modalità sviluppo è sufficiente eseguire:

```bash
pip install -e .[test]
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

## Interfaccia a riga di comando

Dopo l'installazione il comando `trumetrapla` è disponibile nel tuo ambiente Python:

```bash
trumetrapla produzione.xlsx
```

Opzioni principali:

- `--sheet`: nome o indice del foglio Excel da analizzare.
- `--column`: associazione esplicita tra un campo canonico (`date`, `employee`, `process`, `quantity`, `duration_minutes`) e la colonna nel file.
- `--alias`: aggiunge alias personalizzati per l'autoricnoscimento delle colonne.

Esempio di mappatura personalizzata:

```bash
trumetrapla produzione.xlsx --column quantity "Pezzi prodotti" --alias employee Operatore
```

## Branch di sincronizzazione

Per evitare l'errore `fatal: couldn't find remote ref PSite` durante le operazioni automatiche di fetch, il repository include un workflow GitHub Actions che mantiene aggiornato il branch `PSite` sincronizzandolo con l'ultimo commit dei branch principali (`work`, `main` o `master`). In questo modo gli script esterni che fanno riferimento a `PSite` troveranno sempre la relativa ref remota.
