# HEIC → JPG

Programma da riga di comando (senza interfaccia grafica) che converte tutte le foto
`.heic` / `.heif` di una cartella in `.jpg` e le salva in una cartella di destinazione.
Mantiene l'orientamento e i dati EXIF (data, fotocamera…).

## Installazione (una sola volta)

1. Installa **Python 3** da <https://www.python.org/downloads/>
   (su Windows spunta **"Add Python to PATH"** durante l'installazione).
2. Scarica questa cartella (su GitHub: *Code → Download ZIP*, poi estrai).
3. Apri il terminale nella cartella `heic-to-jpg` e installa le librerie:

```
pip install -r requirements.txt
```

## Uso

```
python converti.py CARTELLA_ORIGINE CARTELLA_DESTINAZIONE
```

Esempio Windows:
```
python converti.py "C:\Users\Mario\Pictures\iPhone" "C:\Users\Mario\Pictures\JPG"
```

Esempio Mac/Linux:
```
python3 converti.py ~/Pictures/iPhone ~/Pictures/JPG
```

La cartella di destinazione viene creata se non esiste.

### Opzioni

| Opzione         | Effetto                                         |
|-----------------|-------------------------------------------------|
| `--qualita 95`  | Qualità del JPG da 1 a 100 (default 90)         |
| `--ricorsivo`   | Converte anche le foto nelle sottocartelle      |
| `--sovrascrivi` | Riconverte anche i file già presenti            |
