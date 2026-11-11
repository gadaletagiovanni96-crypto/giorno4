# Convertitore foto e video iPhone

Programma da riga di comando che converte:

- **foto** `.heic` / `.heif` → `.jpg` (mantiene orientamento e dati EXIF)
- **video HEVC** (`.mov`, `.mp4`, `.mkv`…) → `.mp4` H.264, che si apre su qualsiasi PC, TV o telefono.
  I video HDR dell'iPhone vengono convertiti con i colori corretti.

I video che non sono HEVC vengono saltati. Non serve installare ffmpeg a parte: lo installa pip.

## Installazione (una sola volta)

1. Installa **Python 3** da <https://www.python.org/downloads/>
   (su Windows spunta **"Add python.exe to PATH"** durante l'installazione).
2. Scarica questa cartella (su GitHub: *Code → Download ZIP*, poi estrai).
3. Apri il terminale nella cartella `heic-to-jpg` e installa le librerie:

```
py -m pip install -r requirements.txt
```

(Su Mac/Linux: `python3 -m pip install -r requirements.txt`)

## Uso facile (menu)

```
py converti.py
```

Il programma ti chiede tutto, una domanda alla volta:

```
============================================
   CONVERTITORE FOTO E VIDEO iPHONE
============================================
Cosa vuoi convertire?
  1) Foto  HEIC -> JPG
  2) Video HEVC -> MP4
  3) Foto e video
  0) Esci
Scelta [3]:

Cartella di ORIGINE: C:\Foto\iPhone
Cartella di DESTINAZIONE: C:\Foto\Convertite

Qualità JPG da 1 a 100 [90]:
Qualità video:
  1) Alta  (file più grandi)
  2) Media (consigliata)
  3) Bassa (file più piccoli)
Scelta [2]:
Includere le sottocartelle? [s/N]:
Sovrascrivere i file già convertiti? [s/N]:
Avviare la conversione? [S/n]:
```

- Premi **Invio** per usare il valore tra parentesi.
- Puoi **trascinare la cartella** nella finestra del terminale invece di scrivere il percorso.
- La cartella di origine può stare ovunque; quella di destinazione viene creata se non esiste.
- I video richiedono più tempo delle foto (anche alcuni minuti per video lunghi).

## Uso rapido (tutto in un comando)

```
py converti.py "C:\Foto\iPhone" "C:\Foto\Convertite" --tipo tutto --qualita-video media
```

| Opzione                     | Effetto                                          |
|-----------------------------|--------------------------------------------------|
| `--tipo foto/video/tutto`   | Cosa convertire (default `tutto`)                |
| `--qualita 95`              | Qualità JPG da 1 a 100 (default 90)              |
| `--qualita-video alta`      | `alta`, `media` (default) o `bassa`              |
| `--ricorsivo`               | Converte anche nelle sottocartelle               |
| `--sovrascrivi`             | Riconverte anche i file già presenti             |
