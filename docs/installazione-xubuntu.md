# Installazione rapida di TruMetraPla su Xubuntu

Questa guida riassume i passaggi necessari per scaricare, generare e installare TruMetraPla su Xubuntu (o su altre distribuzioni basate su Ubuntu 22.04+).

## Procedura rapida

### Prerequisiti

```bash
sudo apt update
sudo apt install -y python3-venv python3-full desktop-file-utils
```

### Build del pacchetto Linux in ambiente isolato

```bash
cd ~/Scaricati/TruMetraPla-master
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .[build]
trumetrapla build-linux
```

Al termine viene generato l'archivio `dist/TruMetraPla-linux.tar.gz`.

### Installazione del pacchetto

```bash
cd dist
tar -xf TruMetraPla-linux.tar.gz
cd TruMetraPla-linux
# opzionale: installazione in percorso personalizzato
# PREFIX="$HOME/.local" BIN_DEST="$HOME/.local/bin" sudo -E ./install.sh
sudo ./install.sh
```

## Note utili

- Per cambiare percorso senza modificare lo script:

  ```bash
  PREFIX="$HOME/.local" BIN_DEST="$HOME/.local/bin" ./install.sh
  ```

- Usa `sudo -E` solo se servono permessi amministrativi nelle destinazioni scelte.
- Se durante l'installazione delle dipendenze compare l'errore `externally-managed-environment`, assicurati di aver attivato l'ambiente virtuale prima di eseguire `pip install .[build]`.

## Automazione Windows

Per completezza, puoi utilizzare lo script batch incluso per generare rapidamente il pacchetto Windows:

```bat
installer\Build-TruMetraPla.bat --dist C:\Percorso\Output
```

Questo comando sfrutta l'infrastruttura di build già presente nel repository per creare gli artefatti destinati a Windows.
