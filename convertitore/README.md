# Strumenti per foto e video

Programma da terminale con **quattro strumenti**, scelti da un menu che si usa con le **frecce ↑ ↓** e **Invio**:

| Strumento | Cosa fa |
|-----------|---------|
| **iPhone** | foto `.heic` → `.jpg` e video HEVC → `.mp4` (gli altri video vengono saltati) |
| **Qualsiasi foto → JPG** | PNG, WEBP, HEIC, AVIF, TIFF, BMP, GIF, PSD, ICO, TGA… → `.jpg` |
| **Qualsiasi video → MP4** | MOV, AVI, MKV, WMV, WEBM, FLV, 3GP, MPG, TS… → `.mp4` |
| **Mescola** | mette un numero casuale davanti al nome dei file (`foto.jpg` → `042_foto.jpg`), così ordinandoli per nome sono in ordine casuale |

Dettagli:
- Le foto vengono raddrizzate e mantengono i dati EXIF; le parti trasparenti diventano bianche;
  di GIF animate e TIFF multipagina viene salvata la prima immagine.
- I video diventano MP4 H.264 + audio AAC, che si apre su qualsiasi PC, TV o telefono.
  Se un video è già H.264 viene solo "travasato" in MP4: velocissimo e senza perdita di qualità.
  I video HDR dell'iPhone vengono convertiti con i colori corretti.
- I file già convertiti vengono saltati.
- Puoi scegliere **dove salvare** i file convertiti:
  - in **un'altra cartella** (gli originali restano come sono);
  - nella **stessa cartella, accanto agli originali**;
  - nella **stessa cartella, sostituendo gli originali**: ⚠ ogni originale convertito con
    successo viene **eliminato definitivamente** (non va nel cestino). Il programma lo
    avvisa e chiede conferma. I file saltati o con errori non vengono toccati.
- Se due file hanno lo stesso nome (`foto.png` e `foto.webp`) diventano `foto_png.jpg` e `foto_webp.jpg`.
- Non serve installare ffmpeg a parte: lo installa pip.

### Un solo file

Nei tre convertitori, al posto della cartella puoi indicare **una singola foto o un singolo video**.
In quel caso viene convertito solo quel file, nella **sua stessa cartella e con lo stesso nome**
(cambia solo l'estensione, es. `IMG_1234.HEIC` → `IMG_1234.jpg`), e ⚠ **l'originale viene
sovrascritto**. Le domande su destinazione e sottocartelle vengono saltate.
Se indichi una cartella, tutto funziona come sempre.

### Mescola

- Funziona con **qualsiasi tipo di file** della cartella (non entra nelle sottocartelle;
  ignora i file nascosti e i file di sistema come `Thumbs.db`).
- Puoi scegliere se **copiare** i file mescolati in un'altra cartella (gli originali
  restano intatti) oppure **rinominarli** direttamente nella stessa cartella.
- I numeri non si ripetono e hanno tutti le stesse cifre (`001`, `002`… oppure `0001`
  se i file sono più di 999), così l'ordine per nome funziona su ogni sistema.
- Se rimescoli una cartella già mescolata, il vecchio numero viene **sostituito**,
  non se ne aggiunge un secondo.

## Installazione (una sola volta)

1. Installa **Python 3** da <https://www.python.org/downloads/>
   (su Windows spunta **"Add python.exe to PATH"** durante l'installazione).
2. Scarica questa cartella (su GitHub: *Code → Download ZIP*, poi estrai).
3. Apri il terminale nella cartella `convertitore` e installa il programma:

```
py -m pip install .
```

(Su Mac/Linux: `python3 -m pip install .` — il punto finale è importante.)

Fatto: da ora puoi aprire il terminale **in qualsiasi cartella** e scrivere

```
converti
```

Suggerimento: in Esplora file apri la cartella con le foto, scrivi `cmd` nella barra degli
indirizzi e premi Invio; poi scrivi `converti` e, quando chiede la cartella di origine,
premi solo **Invio** per usare la cartella in cui ti trovi.

- Se Windows risponde che `converti` non è riconosciuto, usa `py -m converti`
  (funziona allo stesso modo da qualsiasi cartella), oppure reinstalla Python
  spuntando "Add python.exe to PATH".
- **Per aggiornare** a una nuova versione: scarica il nuovo ZIP ed esegui di nuovo
  `py -m pip install .` nella cartella `convertitore`.
- Per disinstallare: `py -m pip uninstall convertitore`.
- Puoi sempre avviarlo anche senza installarlo, dalla sua cartella, con `py converti.py`
  (in quel caso servono le librerie: `py -m pip install -r requirements.txt`).

## Uso facile (menu con le frecce)

```
converti
```

```
? Quale strumento vuoi usare? (usa le frecce ↑ ↓ e premi Invio)
 ❯ iPhone: foto HEIC -> JPG e video HEVC -> MP4
   Qualsiasi foto -> JPG
   Qualsiasi video -> MP4
   Mescola: numero casuale davanti al nome dei file
   Esci
```

Per i convertitori ti chiede cartella di origine, cartella di destinazione, qualità, sottocartelle,
ti mostra un riepilogo e parte.

- Per le cartelle puoi scrivere il percorso, **trascinare la cartella** nella finestra
  oppure usare **Tab** per completare il nome.
- La cartella di origine può stare ovunque; quella di destinazione viene creata se non esiste.
- Se il terminale non supporta le frecce, il programma mostra automaticamente un menu numerato.

## Uso rapido (tutto in un comando)

```
converti "C:\Foto\Origine" "C:\Foto\Convertite" --strumento video
converti "C:\Foto\Origine" "C:\Foto\Mescolate" --strumento mescola
converti "C:\Foto\Origine" --strumento mescola --rinomina
converti "C:\Foto\Origine" "C:\Foto\Origine" --strumento foto
converti "C:\Foto\Origine" --strumento foto --sostituisci
converti "C:\Foto\IMG_1234.HEIC"                      (un solo file, sul posto)
converti "C:\Video\vacanza.avi" --strumento video     (un solo file, sul posto)
converti .                                             (la cartella in cui ti trovi)
```

| Opzione                         | Effetto                                              |
|---------------------------------|------------------------------------------------------|
| `--strumento iphone/foto/video/mescola` | Quale strumento usare (default `iphone`)     |
| `--tipo foto/video/tutto`       | Solo per `iphone`: cosa convertire (default `tutto`) |
| `--qualita 95`                  | Qualità JPG da 1 a 100 (default 90)                  |
| `--qualita-video alta`          | `alta`, `media` (default) o `bassa`                  |
| `--ricorsivo`                   | Converte anche nelle sottocartelle                   |
| `--sovrascrivi`                 | Riconverte anche i file già presenti                 |
| `--sostituisci`                 | Salva nella cartella di origine ed ⚠ ELIMINA gli originali convertiti |
| `--rinomina`                    | Solo per `mescola`: rinomina sul posto invece di copiare |
