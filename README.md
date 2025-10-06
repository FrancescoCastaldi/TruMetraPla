# TruMetraPla

TruMetraPla monitora la produttività nei processi metalmeccanici, importando dati da file Excel e mostrando una dashboard con KPI, grafici e analisi su quantità, tipologia di processo e rendimento dei dipendenti.

## Branch di sincronizzazione

Per evitare l'errore `fatal: couldn't find remote ref PSite` durante le operazioni automatiche di fetch, il repository include ora un workflow GitHub Actions che mantiene aggiornato il branch `PSite` sincronizzandolo con l'ultimo commit dei branch principali (`work`, `main` o `master`). In questo modo gli script esterni che fanno riferimento a `PSite` troveranno sempre la relativa ref remota.
