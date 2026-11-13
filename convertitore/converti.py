#!/usr/bin/env python3
"""Convertitore di foto e video con quattro strumenti:

  1. iPhone        foto HEIC -> JPG e video HEVC -> MP4
  2. Foto -> JPG   qualsiasi foto (PNG, WEBP, HEIC, TIFF, BMP, GIF, AVIF...) in JPG
  3. Video -> MP4  qualsiasi video (MOV, AVI, MKV, WMV, WEBM...) in MP4
  4. Mescola       mette un numero casuale davanti al nome dei file,
                   così ordinandoli per nome risultano in ordine casuale

Uso (dopo "py -m pip install ." basta scrivere "converti" in qualsiasi cartella):
    python converti.py                         (menu con le frecce)
    python converti.py ORIGINE DESTINAZIONE --strumento iphone|foto|video|mescola [opzioni]
    python converti.py ORIGINE --strumento mescola --rinomina   (rinomina sul posto)
    python converti.py FILE --strumento foto|video|iphone        (un solo file: lo
                                     converte sul posto, sostituendo l'originale)
"""
import argparse
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
    from pillow_heif import register_heif_opener
    import imageio_ffmpeg
except ImportError:
    sys.exit("Librerie mancanti. Esegui prima:  py -m pip install -r requirements.txt")

register_heif_opener()

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# ---------------------------------------------------------------- formati

EST_FOTO_IPHONE = {".heic", ".heif"}
EST_VIDEO_IPHONE = {".mov", ".mp4", ".m4v", ".mkv", ".hevc", ".h265", ".265"}

EST_FOTO_TUTTE = {".heic", ".heif", ".png", ".webp", ".bmp", ".tif", ".tiff",
                  ".gif", ".avif", ".jfif", ".ico", ".tga", ".psd", ".jp2",
                  ".ppm", ".pgm", ".pbm", ".pcx", ".dib"}
EST_VIDEO_TUTTE = {".mov", ".mp4", ".m4v", ".mkv", ".avi", ".wmv", ".webm",
                   ".flv", ".f4v", ".3gp", ".3g2", ".mpg", ".mpeg", ".m2v",
                   ".ts", ".mts", ".m2ts", ".vob", ".ogv", ".asf", ".divx",
                   ".hevc", ".h265", ".265", ".h264", ".264"}

QUALITA_VIDEO = {"alta": 18, "media": 23, "bassa": 28}  # più basso = migliore

STRUMENTI = {
    "iphone": "iPhone: foto HEIC -> JPG e video HEVC -> MP4",
    "foto": "Qualsiasi foto -> JPG",
    "video": "Qualsiasi video -> MP4",
    "mescola": "Mescola: numero casuale davanti al nome dei file",
}

FILE_DI_SISTEMA = {"thumbs.db", "desktop.ini", ".ds_store"}


# ---------------------------------------------------------------- foto

def converti_foto(sorgente: Path, destinazione: Path, qualita: int) -> None:
    with Image.open(sorgente) as originale:
        originale.seek(0)  # GIF animate / TIFF multipagina: primo fotogramma
        img = ImageOps.exif_transpose(originale)  # raddrizza la foto
        exif = img.info.get("exif")  # dati EXIF con l'orientamento già corretto

        if img.mode.startswith("I"):  # immagini a 16 bit
            img = img.point(lambda v: v / 256).convert("L")
        if img.mode in ("RGBA", "LA", "PA") or (
                img.mode == "P" and "transparency" in img.info):
            # il JPG non ha trasparenza: metto uno sfondo bianco
            img = img.convert("RGBA")
            sfondo = Image.new("RGB", img.size, (255, 255, 255))
            sfondo.paste(img, mask=img.getchannel("A"))
            img = sfondo
        else:
            img = img.convert("RGB")

        opzioni = {"quality": qualita}
        if exif:
            opzioni["exif"] = exif
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        img.save(destinazione, "JPEG", **opzioni)


# ---------------------------------------------------------------- video

def filtro_hdr(trasferimento: str) -> str:
    """Converte i colori HDR in colori normali (altrimenti il video è sbiadito)."""
    return (f"zscale=tin={trasferimento}:pin=bt2020:min=bt2020nc:t=linear:npl=100,"
            "format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def info_video(file: Path) -> dict:
    """Legge codec video, codec audio e tipo di HDR del file."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(file)],
                       capture_output=True, text=True, errors="replace")
    info = {"video": None, "audio": None, "hdr": None}
    v = re.search(r"Stream #.*?Video: (.*)", r.stderr)
    a = re.search(r"Stream #.*?Audio: (\w+)", r.stderr)
    if a:
        info["audio"] = a.group(1)
    if v:
        testo = v.group(1)
        info["video"] = testo.split()[0].strip(",")
        if "arib-std-b67" in testo:      # HLG: quello dei video iPhone
            info["hdr"] = "arib-std-b67"
        elif "smpte2084" in testo:       # PQ / HDR10
            info["hdr"] = "smpte2084"
        elif "bt2020" in testo:
            info["hdr"] = "arib-std-b67"
    return info


def converti_video(sorgente: Path, destinazione: Path, crf: int, info: dict,
                   copia_se_possibile: bool) -> None:
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    temporaneo = destinazione.with_name(destinazione.stem + ".parziale.mp4")

    def esegui(copia_video: bool, con_hdr: bool, silenzioso: bool) -> int:
        cmd = [FFMPEG, "-hide_banner", "-loglevel", "quiet" if silenzioso else "error",
               "-stats", "-y", "-i", str(sorgente),
               "-map", "0:v:0", "-map", "0:a:0?", "-map_metadata", "0"]
        if copia_video:
            cmd += ["-c:v", "copy"]
        else:
            if con_hdr:
                cmd += ["-vf", filtro_hdr(info["hdr"])]
            cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                    "-pix_fmt", "yuv420p"]
        if copia_video and info["audio"] in ("aac", "mp3"):
            cmd += ["-c:a", "copy"]
        else:
            cmd += ["-c:a", "aac", "-b:a", "192k"]
        cmd += ["-movflags", "+faststart", str(temporaneo)]
        return subprocess.run(cmd).returncode

    # Tentativi in ordine, dal più veloce/migliore al più sicuro
    tentativi = []
    if copia_se_possibile and info["video"] == "h264" and not info["hdr"]:
        tentativi.append((True, False, "Video già H.264: lo copio senza ricomprimerlo"))
    if info["hdr"]:
        tentativi.append((False, True, None))
    tentativi.append((False, False, None))

    try:
        for n, (copia, hdr, messaggio) in enumerate(tentativi):
            if messaggio:
                print(f"    {messaggio}")
            ultimo = n == len(tentativi) - 1
            if esegui(copia, hdr, silenzioso=not ultimo) == 0:
                temporaneo.replace(destinazione)
                return
            if not ultimo:
                print("\n    Primo tentativo non riuscito, riprovo in modo diverso...")
        raise RuntimeError("ffmpeg non è riuscito a convertire il video")
    finally:
        if temporaneo.exists():
            temporaneo.unlink()


# ---------------------------------------------------------------- logica comune

def trova_file(cartella: Path, estensioni: set, ricorsivo: bool) -> list:
    pattern = "**/*" if ricorsivo else "*"
    return sorted(f for f in cartella.glob(pattern)
                  if f.is_file() and f.suffix.lower() in estensioni
                  and ".parziale." not in f.name)


def estensioni_strumento(strumento: str) -> set:
    return {"iphone": EST_FOTO_IPHONE | EST_VIDEO_IPHONE,
            "foto": EST_FOTO_TUTTE,
            "video": EST_VIDEO_TUTTE}[strumento]


def elenca_file(args, estensioni: set) -> list:
    """Un solo file se l'utente ha indicato un file, altrimenti la cartella."""
    singolo = getattr(args, "file", None)
    if singolo is not None:
        return [singolo] if singolo.suffix.lower() in estensioni else []
    return trova_file(args.origine, estensioni, args.ricorsivo)


def prepara_file_singolo(args) -> None:
    """Un solo file: si converte nella sua cartella, con lo stesso nome,
    sostituendo l'originale (e un eventuale file convertito già presente)."""
    args.file = args.origine
    args.origine = args.destinazione = args.file.parent
    args.sostituisci = True
    args.sovrascrivi = True
    args.ricorsivo = False
    if args.strumento == "iphone":
        args.tipo = "foto" if args.file.suffix.lower() in EST_FOTO_IPHONE else "video"


def mappa_uscite(files: list, args, estensione: str) -> list:
    """Abbina a ogni file il percorso di uscita. Se due file hanno lo stesso
    nome (es. foto.png e foto.webp) aggiunge il formato: foto_png.jpg."""
    base = [args.destinazione / f.relative_to(args.origine).with_suffix(estensione)
            for f in files]
    conteggi = {}
    for out in base:
        conteggi[out] = conteggi.get(out, 0) + 1
    coppie = []
    for f, out in zip(files, base):
        if conteggi[out] > 1:
            out = out.with_name(f"{out.stem}_{f.suffix[1:].lower()}{estensione}")
        if out.resolve() == f.resolve() and not args.sostituisci:
            # stesso nome dell'originale (es. video.mp4): non lo tocco
            out = out.with_name(out.stem + "_convertito" + estensione)
        coppie.append((f, out))
    return coppie


def gia_presente(f: Path, out: Path, args) -> bool:
    return out.exists() and out.resolve() != f.resolve() and not args.sovrascrivi


def elimina_originale(f: Path, out: Path, args) -> str:
    """In modalità 'sostituisci' cancella l'originale, ma solo se il file
    convertito esiste davvero e non è vuoto."""
    if not args.sostituisci or out.resolve() == f.resolve():
        return ""
    if out.is_file() and out.stat().st_size > 0:
        f.unlink()
        return "  (originale eliminato)"
    return "  (originale mantenuto: il file convertito sembra vuoto)"


def elabora_foto(args, estensioni: set) -> list:
    files = elenca_file(args, estensioni)
    print(f"\n--- FOTO: {len(files)} file trovati ---")
    conteggio = [0, 0, 0]  # convertiti, saltati, errori
    for i, (f, out) in enumerate(mappa_uscite(files, args, ".jpg"), 1):
        nome = out.relative_to(args.destinazione)
        if gia_presente(f, out, args):
            print(f"[{i}/{len(files)}] Già presente, salto: {nome}")
            conteggio[1] += 1
            continue
        try:
            converti_foto(f, out, args.qualita)
            nota = elimina_originale(f, out, args)
            print(f"[{i}/{len(files)}] OK: {f.name} -> {nome}{nota}")
            conteggio[0] += 1
        except UnidentifiedImageError:
            print(f"[{i}/{len(files)}] ERRORE: {f.name} è danneggiato o non è un'immagine")
            conteggio[2] += 1
        except Exception as e:
            print(f"[{i}/{len(files)}] ERRORE su {f.name}: {e}")
            conteggio[2] += 1
    return conteggio


def elabora_video(args, estensioni: set, solo_hevc: bool) -> list:
    files = elenca_file(args, estensioni)
    print(f"\n--- VIDEO: {len(files)} file trovati ---")
    crf = QUALITA_VIDEO[args.qualita_video]
    conteggio = [0, 0, 0]
    for i, (f, out) in enumerate(mappa_uscite(files, args, ".mp4"), 1):
        nome = out.relative_to(args.destinazione)
        if gia_presente(f, out, args):
            print(f"[{i}/{len(files)}] Già presente, salto: {nome}")
            conteggio[1] += 1
            continue
        info = info_video(f)
        if info["video"] is None:
            print(f"[{i}/{len(files)}] Nessun video leggibile, salto: {f.name}")
            conteggio[1] += 1
            continue
        if solo_hevc and info["video"] != "hevc":
            print(f"[{i}/{len(files)}] Non è HEVC ({info['video']}), salto: {f.name}")
            conteggio[1] += 1
            continue
        if (args.destinazione.resolve() == args.origine.resolve()
                and f.suffix.lower() == ".mp4" and info["video"] == "h264"
                and not info["hdr"] and info["audio"] in (None, "aac", "mp3")):
            print(f"[{i}/{len(files)}] È già un MP4 H.264, salto: {f.name}")
            conteggio[1] += 1
            continue
        print(f"[{i}/{len(files)}] Converto {f.name} ({info['video']}"
              f"{', HDR' if info['hdr'] else ''})... può richiedere qualche minuto")
        try:
            converti_video(f, out, crf, info, copia_se_possibile=not solo_hevc)
            print(f"    OK -> {nome}{elimina_originale(f, out, args)}")
            conteggio[0] += 1
        except Exception as e:
            print(f"    ERRORE: {e}")
            conteggio[2] += 1
    return conteggio


# ---------------------------------------------------------------- mescola

def file_da_mescolare(cartella: Path) -> list:
    return sorted(f for f in cartella.iterdir()
                  if f.is_file() and not f.name.startswith(".")
                  and f.name.lower() not in FILE_DI_SISTEMA)


def togli_vecchio_numero(files: list) -> list:
    """Se TUTTI i file hanno già un numero davanti della stessa lunghezza
    (es. 007_foto.jpg), vuol dire che erano già stati mescolati: tolgo il
    vecchio numero, così non se ne accumulano due."""
    trovati = [re.match(r"^(\d+)_(.+)$", f.name) for f in files]
    if files and all(trovati) and len({len(m.group(1)) for m in trovati}) == 1:
        return [m.group(2) for m in trovati]
    return [f.name for f in files]


def mescola(origine: Path, destinazione: Path | None) -> int:
    """destinazione=None significa: rinomina i file nella cartella di origine."""
    files = file_da_mescolare(origine)
    print(f"\n--- MESCOLA: {len(files)} file trovati ---")
    if not files:
        return 0

    nomi = togli_vecchio_numero(files)
    numeri = list(range(1, len(files) + 1))
    random.shuffle(numeri)
    cifre = max(3, len(str(len(files))))  # 001, 002... così l'ordine per nome funziona
    nuovi = [f"{n:0{cifre}d}_{nome}" for n, nome in zip(numeri, nomi)]
    coppie = sorted(zip(files, nuovi), key=lambda c: c[1])

    ok = saltati = errori = 0
    if destinazione is not None:
        destinazione.mkdir(parents=True, exist_ok=True)
        for i, (f, nuovo) in enumerate(coppie, 1):
            out = destinazione / nuovo
            if out.exists():
                print(f"[{i}/{len(files)}] Esiste già, salto: {nuovo}")
                saltati += 1
                continue
            try:
                shutil.copy2(f, out)
                print(f"[{i}/{len(files)}] {f.name} -> {nuovo}")
                ok += 1
            except Exception as e:
                print(f"[{i}/{len(files)}] ERRORE su {f.name}: {e}")
                errori += 1
    else:
        # Due passaggi (prima nomi temporanei, poi definitivi) per evitare
        # che un nuovo nome coincida con quello di un file non ancora rinominato.
        temporanei = []
        for i, (f, nuovo) in enumerate(coppie):
            tmp = f.with_name(f".mescola_{i}_{f.name}")
            try:
                f.rename(tmp)
                temporanei.append((f, tmp, nuovo))
            except Exception as e:
                print(f"ERRORE su {f.name}: {e}")
                errori += 1
        for i, (f, tmp, nuovo) in enumerate(temporanei, 1):
            try:
                tmp.rename(f.with_name(nuovo))
                print(f"[{i}/{len(temporanei)}] {f.name} -> {nuovo}")
                ok += 1
            except Exception as e:
                tmp.rename(f)  # rimetto il nome originale
                print(f"[{i}/{len(temporanei)}] ERRORE su {f.name}: {e}")
                errori += 1

    print(f"\nFatto. Mescolati: {ok}  Saltati: {saltati}  Errori: {errori}")
    return 1 if errori else 0


def converti(args) -> int:
    if args.strumento == "mescola":
        return mescola(args.origine, None if args.rinomina else args.destinazione)
    risultati = []
    if args.strumento == "iphone":
        if args.tipo in ("foto", "tutto"):
            risultati.append(elabora_foto(args, EST_FOTO_IPHONE))
        if args.tipo in ("video", "tutto"):
            risultati.append(elabora_video(args, EST_VIDEO_IPHONE, solo_hevc=True))
    elif args.strumento == "foto":
        risultati.append(elabora_foto(args, EST_FOTO_TUTTE))
    else:
        risultati.append(elabora_video(args, EST_VIDEO_TUTTE, solo_hevc=False))
    ok, saltati, errori = (sum(c) for c in zip(*risultati))
    print(f"\nFatto. Convertiti: {ok}  Saltati: {saltati}  Errori: {errori}")
    return 1 if errori else 0


# ---------------------------------------------------------------- menu con le frecce

try:
    import questionary
    from questionary import Choice, Style
    STILE = Style([
        ("qmark", "fg:#00b4d8 bold"),
        ("question", "bold"),
        ("pointer", "fg:#00b4d8 bold"),
        ("highlighted", "fg:#00b4d8 bold"),
        ("selected", "fg:#00b4d8"),
        ("answer", "fg:#2a9d8f bold"),
        ("instruction", "fg:#888888 italic"),
    ])
except ImportError:
    questionary = None

USA_FRECCE = questionary is not None and sys.stdin.isatty() and sys.stdout.isatty()


def scegli(domanda: str, opzioni: list, default=None):
    """opzioni = [(valore, testo), ...]. Menu con le frecce, oppure numerato
    se il terminale non lo supporta."""
    global USA_FRECCE
    if USA_FRECCE:
        try:
            scelte = [Choice(testo, value=valore) for valore, testo in opzioni]
            iniziale = next((c for c in scelte if c.value == default), None)
            return questionary.select(
                domanda, choices=scelte, default=iniziale, style=STILE,
                qmark="?", pointer="❯",
                instruction="(usa le frecce ↑ ↓ e premi Invio)").unsafe_ask()
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception:
            USA_FRECCE = False  # terminale non compatibile: uso i numeri
    print(domanda)
    for n, (_, testo) in enumerate(opzioni, 1):
        print(f"  {n}) {testo}")
    indice_def = next((n for n, (v, _) in enumerate(opzioni, 1) if v == default), 1)
    while True:
        r = input(f"Scelta [{indice_def}]: ").strip() or str(indice_def)
        if r.isdigit() and 1 <= int(r) <= len(opzioni):
            return opzioni[int(r) - 1][0]
        print("  Scelta non valida, riprova.")


def si_no(domanda: str, default: bool) -> bool:
    return scegli(domanda, [(True, "Sì"), (False, "No")], default)


def pulisci_percorso(testo: str) -> str:
    testo = testo.strip()
    if testo.startswith("& "):  # PowerShell aggiunge "& " quando trascini
        testo = testo[2:]
    return testo.strip().strip('"').strip("'").strip()


def chiedi_cartella(domanda: str, deve_esistere: bool,
                    estensioni_file: set | None = None,
                    vuoto_corrente: bool = False) -> Path:
    """Chiede una cartella. Se estensioni_file è indicato, accetta anche un
    singolo file con una di quelle estensioni. Con vuoto_corrente=True,
    premendo solo Invio si usa la cartella in cui è aperto il terminale."""
    accetta_file = estensioni_file is not None
    while True:
        if USA_FRECCE:
            try:
                cosa = "la cartella o il file" if accetta_file else "la cartella"
                extra = "; Invio = cartella corrente" if vuoto_corrente else ""
                print(f"  (scrivi il percorso o trascina qui {cosa}; Tab completa il nome{extra})")
                testo = questionary.path(
                    domanda, only_directories=not accetta_file, style=STILE, qmark="?"
                ).unsafe_ask()
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception:
                testo = input(domanda + " ")
        else:
            testo = input(domanda + " ")
        testo = pulisci_percorso(testo)
        if not testo and vuoto_corrente:
            print(f"  Uso la cartella corrente: {Path.cwd()}")
            return Path.cwd()
        if not testo:
            print("  Scrivi un percorso (puoi anche trascinare qui la cartella).")
            continue
        cartella = Path(testo).expanduser()
        if accetta_file and cartella.is_file():
            if cartella.suffix.lower() in estensioni_file:
                return cartella
            print(f"  Questo strumento non converte i file '{cartella.suffix}', riprova.")
            continue
        if deve_esistere and not cartella.is_dir():
            print(f"  La cartella '{cartella}' non esiste, riprova.")
            continue
        return cartella


def chiedi_dove_salvare(origine: Path) -> tuple:
    """Restituisce (cartella di destinazione, sostituire gli originali?)."""
    while True:
        modo = scegli("Dove vuoi salvare i file convertiti?", [
            ("altra", "In un'altra cartella (gli originali restano come sono)"),
            ("accanto", "Nella stessa cartella, accanto agli originali"),
            ("sostituisci", "Nella stessa cartella, SOSTITUENDO gli originali"),
        ], "altra")
        if modo == "accanto":
            return origine, False
        if modo == "sostituisci":
            print("\n  ⚠  ATTENZIONE: ogni file convertito con successo prenderà il posto")
            print("     dell'originale, che verrà ELIMINATO definitivamente")
            print("     (non finisce nel cestino). I file saltati o con errori restano.\n")
            if si_no("Sei sicuro di voler sostituire gli originali?", False):
                return origine, True
            print()
            continue
        destinazione = chiedi_cartella("Cartella di DESTINAZIONE:", deve_esistere=False)
        if destinazione.resolve() != origine.resolve():
            return destinazione, False
        print("  È la stessa cartella di origine: scegli una delle opzioni \"stessa cartella\".\n")


def menu_mescola() -> None:
    origine = chiedi_cartella("Cartella con i file da mescolare:", deve_esistere=True,
                              vuoto_corrente=True)
    modo = scegli("Come vuoi ottenere i file mescolati?", [
        ("copia", "Copia in un'altra cartella (gli originali restano come sono)"),
        ("rinomina", "Rinomina i file nella stessa cartella"),
    ], "copia")
    destinazione = None
    if modo == "copia":
        while True:
            destinazione = chiedi_cartella("Cartella di DESTINAZIONE:", deve_esistere=False)
            if destinazione.resolve() != origine.resolve():
                break
            print("  Deve essere diversa dall'origine (per rinominare sul posto scegli l'altra opzione).")

    n = len(file_da_mescolare(origine))
    print("\nRiepilogo:")
    print(f"  Strumento:     {STRUMENTI['mescola']}")
    print(f"  Cartella:      {origine}  ({n} file)")
    if destinazione:
        print(f"  Copia in:      {destinazione}")
        if destinazione.is_dir() and any(destinazione.iterdir()):
            print("  Attenzione:    la cartella di destinazione non è vuota")
    else:
        print("  Modo:          rinomina sul posto")
    print("  Esempio:       foto.jpg -> 042_foto.jpg\n")

    if si_no("Avviare?", True):
        mescola(origine, destinazione)
    else:
        print("Annullato.")


def modalita_interattiva() -> int:
    while True:
        print("\n" + "=" * 46)
        print("        STRUMENTI PER FOTO E VIDEO")
        print("=" * 46 + "\n")

        strumento = scegli("Quale strumento vuoi usare?", [
            ("iphone", STRUMENTI["iphone"]),
            ("foto", STRUMENTI["foto"]),
            ("video", STRUMENTI["video"]),
            ("mescola", STRUMENTI["mescola"]),
            (None, "Esci"),
        ], "iphone")
        if strumento is None:
            return 0
        if strumento == "mescola":
            menu_mescola()
            print()
            if not si_no("Vuoi fare un'altra operazione?", False):
                return 0
            continue

        origine = chiedi_cartella("Cartella di ORIGINE (o una singola foto/video):",
                                  deve_esistere=True,
                                  estensioni_file=estensioni_strumento(strumento),
                                  vuoto_corrente=True)
        singolo = origine.is_file()

        tipo = "tutto"
        if strumento == "iphone":
            if singolo:
                tipo = "foto" if origine.suffix.lower() in EST_FOTO_IPHONE else "video"
            else:
                tipo = scegli("Cosa vuoi convertire?", [
                    ("tutto", "Foto e video"),
                    ("foto", "Solo foto  (HEIC -> JPG)"),
                    ("video", "Solo video (HEVC -> MP4)"),
                ], "tutto")
        if singolo and strumento in ("foto", "video"):
            tipo = strumento

        fa_foto = strumento == "foto" or (strumento == "iphone" and tipo != "video")
        fa_video = strumento == "video" or (strumento == "iphone" and tipo != "foto")

        if singolo:
            destinazione, sostituisci = origine.parent, True
        else:
            destinazione, sostituisci = chiedi_dove_salvare(origine)

        qualita, qualita_video = 90, "media"
        if fa_foto:
            qualita = scegli("Qualità delle foto JPG:", [
                (95, "Massima (95)"),
                (90, "Alta    (90)  - consigliata"),
                (80, "Media   (80)"),
                (70, "Bassa   (70)  - file più piccoli"),
            ], 90)
        if fa_video:
            qualita_video = scegli("Qualità dei video:", [
                ("alta", "Alta   - file più grandi"),
                ("media", "Media  - consigliata"),
                ("bassa", "Bassa  - file più piccoli"),
            ], "media")
        ricorsivo = sovrascrivi = False
        if not singolo:
            ricorsivo = si_no("Includere le sottocartelle?", False)
            sovrascrivi = si_no("Sovrascrivere i file già convertiti?", False)

        argomenti = argparse.Namespace(
            strumento=strumento, tipo=tipo,
            origine=origine, destinazione=destinazione,
            qualita=qualita, qualita_video=qualita_video,
            ricorsivo=ricorsivo, sovrascrivi=sovrascrivi,
            sostituisci=sostituisci)

        print("\nRiepilogo:")
        print(f"  Strumento:     {STRUMENTI[strumento]}")
        if singolo:
            nuovo = origine.with_suffix(".jpg" if fa_foto else ".mp4").name
            print(f"  File:          {origine}")
            print(f"  Diventa:       {nuovo}  (nella stessa cartella)")
            if fa_foto:
                print(f"  Qualità foto:  {qualita}")
            else:
                print(f"  Qualità video: {qualita_video}")
            print("\n  ⚠  Il file originale verrà SOVRASCRITTO (eliminato e sostituito).")
            print()
            if si_no("Avviare la conversione?", True):
                prepara_file_singolo(argomenti)
                converti(argomenti)
            else:
                print("Annullato.")
            print()
            if not si_no("Vuoi fare un'altra operazione?", False):
                return 0
            continue

        if strumento == "iphone":
            print(f"  Cosa:          {'foto e video' if tipo == 'tutto' else 'solo ' + tipo}")
        print(f"  Origine:       {origine}")
        if destinazione.resolve() != origine.resolve():
            print(f"  Destinazione:  {destinazione}")
        elif sostituisci:
            print("  Destinazione:  stessa cartella, SOSTITUENDO gli originali")
        else:
            print("  Destinazione:  stessa cartella, accanto agli originali")
        if fa_foto:
            print(f"  Qualità foto:  {qualita}")
        if fa_video:
            print(f"  Qualità video: {qualita_video}")
        print(f"  Sottocartelle: {'sì' if ricorsivo else 'no'}")
        print(f"  Sovrascrivi:   {'sì' if sovrascrivi else 'no'}")
        if sostituisci:
            print("\n  ⚠  Gli originali convertiti verranno ELIMINATI.")
        print()

        if si_no("Avviare la conversione?", True):
            converti(argomenti)
        else:
            print("Annullato.")

        print()
        if not si_no("Vuoi fare un'altra operazione?", False):
            return 0


# ---------------------------------------------------------------- avvio

def main() -> int:
    if len(sys.argv) == 1:
        try:
            return modalita_interattiva()
        except (KeyboardInterrupt, EOFError):
            print("\nInterrotto.")
            return 1

    p = argparse.ArgumentParser(description="Converte foto in JPG e video in MP4.")
    p.add_argument("origine", type=Path,
                   help="Cartella con i file da convertire, oppure un singolo file")
    p.add_argument("destinazione", type=Path, nargs="?",
                   help="Cartella dove salvare i file convertiti")
    p.add_argument("--strumento", choices=list(STRUMENTI), default="iphone",
                   help="iphone (default), foto, video o mescola")
    p.add_argument("--sostituisci", action="store_true",
                   help="salva nella cartella di origine ed ELIMINA gli originali convertiti")
    p.add_argument("--rinomina", action="store_true",
                   help="solo per mescola: rinomina i file sul posto invece di copiarli")
    p.add_argument("--tipo", choices=["foto", "video", "tutto"], default="tutto",
                   help="solo per lo strumento iphone (default tutto)")
    p.add_argument("--qualita", type=int, default=90, help="Qualità JPG 1-100 (default 90)")
    p.add_argument("--qualita-video", choices=list(QUALITA_VIDEO), default="media")
    p.add_argument("--ricorsivo", action="store_true", help="Cerca anche nelle sottocartelle")
    p.add_argument("--sovrascrivi", action="store_true", help="Riconverte i file già presenti")
    args = p.parse_args()

    if args.origine.is_file():
        if args.strumento == "mescola":
            print("Errore: mescola funziona solo con una cartella.")
            return 1
        if args.origine.suffix.lower() not in estensioni_strumento(args.strumento):
            print(f"Errore: lo strumento '{args.strumento}' non converte i file "
                  f"'{args.origine.suffix}'.")
            return 1
        if args.destinazione is not None and \
                args.destinazione.resolve() != args.origine.parent.resolve():
            print("Errore: con un singolo file la conversione avviene nella sua cartella; "
                  "non indicare una destinazione.")
            return 1
        if not 1 <= args.qualita <= 100:
            print("Errore: --qualita deve essere tra 1 e 100.")
            return 1
        print("ATTENZIONE: il file originale verrà SOVRASCRITTO (eliminato e sostituito).")
        prepara_file_singolo(args)
        try:
            return converti(args)
        except KeyboardInterrupt:
            print("\nInterrotto.")
            return 1

    if not args.origine.is_dir():
        print(f"Errore: la cartella '{args.origine}' non esiste.")
        return 1
    if args.sostituisci:
        if args.strumento == "mescola":
            print("Errore: per mescola usa --rinomina.")
            return 1
        if args.destinazione is not None and args.destinazione.resolve() != args.origine.resolve():
            print("Errore: --sostituisci funziona solo salvando nella cartella di origine.")
            return 1
        args.destinazione = args.origine
        print("ATTENZIONE: gli originali convertiti con successo verranno ELIMINATI.")
    if args.destinazione is None and not (args.strumento == "mescola" and args.rinomina):
        print("Errore: indica la cartella di destinazione.")
        return 1
    if (args.strumento == "mescola" and not args.rinomina
            and args.destinazione.resolve() == args.origine.resolve()):
        print("Errore: la destinazione deve essere diversa dall'origine (oppure usa --rinomina).")
        return 1
    if not 1 <= args.qualita <= 100:
        print("Errore: --qualita deve essere tra 1 e 100.")
        return 1
    try:
        return converti(args)
    except KeyboardInterrupt:
        print("\nInterrotto.")
        return 1


def avvia() -> None:
    """Punto di partenza del comando "converti" installato con pip."""
    sys.exit(main())


if __name__ == "__main__":
    codice = main()
    if len(sys.argv) == 1:
        input("\nPremi Invio per chiudere...")  # utile se avviato con doppio clic
    sys.exit(codice)
