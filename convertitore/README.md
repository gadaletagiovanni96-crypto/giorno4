# Convertitore di foto e video

Programma da terminale con **tre strumenti**, scelti da un menu che si usa con le **frecce ↑ ↓** e **Invio**:

| Strumento | Cosa fa |
|-----------|---------|
| **iPhone** | foto `.heic` → `.jpg` e video HEVC → `.mp4` (gli altri video vengono saltati) |
| **Qualsiasi foto → JPG** | PNG, WEBP, HEIC, AVIF, TIFF, BMP, GIF, PSD, ICO, TGA… → `.jpg` |
| **Qualsiasi video → MP4** | MOV, AVI, MKV, WMV, WEBM, FLV, 3GP, MPG, TS… → `.mp4` |

Dettagli:
- Le foto vengono raddrizzate e mantengono i dati EXIF; le parti trasparenti diventano bianche;
  di GIF animate e TIFF multipagina viene salvata la prima immagine.
- I video diventano MP4 H.264 + audio AAC, che si apre su qualsiasi PC, TV o telefono.
  Se un video è già H.264 viene solo "travasato" in MP4: velocissimo e senza perdita di qualità.
  I video HDR dell'iPhone vengono convertiti con i colori corretti.
- Gli originali non vengono mai modificati. I file già convertiti vengono saltati.
- Se due file hanno lo stesso nome (`foto.png` e `foto.webp`) diventano `foto_png.jpg` e `foto_webp.jpg`.
- Non serve installare ffmpeg a parte: lo installa pip.

## Installazione (una sola volta)

1. Installa **Python 3** da <https://www.python.org/downloads/>
   (su Windows spunta **"Add python.exe to PATH"** durante l'installazione).
2. Scarica questa cartella (su GitHub: *Code → Download ZIP*, poi estrai).
3. Apri il terminale nella cartella `convertitore` e installa le librerie:

```
py -m pip install -r requirements.txt
```

(Su Mac/Linux: `python3 -m pip install -r requirements.txt`)

## Uso facile (menu con le frecce)

```
py converti.py
```

```
? Quale strumento vuoi usare? (usa le frecce ↑ ↓ e premi Invio)
 ❯ iPhone: foto HEIC -> JPG e video HEVC -> MP4
   Qualsiasi foto -> JPG
   Qualsiasi video -> MP4
   Esci
```

Poi ti chiede cartella di origine, cartella di destinazione, qualità, sottocartelle,
ti mostra un riepilogo e parte.

- Per le cartelle puoi scrivere il percorso, **trascinare la cartella** nella finestra
  oppure usare **Tab** per completare il nome.
- La cartella di origine può stare ovunque; quella di destinazione viene creata se non esiste.
- Se il terminale non supporta le frecce, il programma mostra automaticamente un menu numerato.

## Uso rapido (tutto in un comando)

```
py converti.py "C:\Foto\Origine" "C:\Foto\Convertite" --strumento video
```

| Opzione                         | Effetto                                              |
|---------------------------------|------------------------------------------------------|
| `--strumento iphone/foto/video` | Quale strumento usare (default `iphone`)             |
| `--tipo foto/video/tutto`       | Solo per `iphone`: cosa convertire (default `tutto`) |
| `--qualita 95`                  | Qualità JPG da 1 a 100 (default 90)                  |
| `--qualita-video alta`          | `alta`, `media` (default) o `bassa`                  |
| `--ricorsivo`                   | Converte anche nelle sottocartelle                   |
| `--sovrascrivi`                 | Riconverte anche i file già presenti                 |
