#!/usr/bin/env python3
"""Converte foto HEIC -> JPG e video HEVC -> MP4 (H.264).

Uso:
    python converti.py                       (menu interattivo)
    python converti.py ORIGINE DESTINAZIONE [opzioni]

Opzioni:
    --tipo foto|video|tutto   cosa convertire (default: tutto)
    --qualita 90              qualità dei JPG, 1-100
    --qualita-video media     alta | media | bassa
    --ricorsivo               cerca anche nelle sottocartelle
    --sovrascrivi             riconverte i file già presenti
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
    from pillow_heif import register_heif_opener
    import imageio_ffmpeg
except ImportError:
    sys.exit("Librerie mancanti. Esegui prima:  py -m pip install -r requirements.txt")

register_heif_opener()

EST_FOTO = {".heic", ".heif"}
EST_VIDEO = {".mov", ".mp4", ".m4v", ".mkv", ".hevc", ".h265", ".265"}

# Più basso = qualità migliore e file più grande
QUALITA_VIDEO = {"alta": 18, "media": 23, "bassa": 28}

# Converte i colori dei video HDR (iPhone) in colori normali, altrimenti
# il video risulterebbe sbiadito su molti lettori.
def filtro_hdr(trasferimento: str) -> str:
    return (f"zscale=tin={trasferimento}:pin=bt2020:min=bt2020nc:t=linear:npl=100,"
            "format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


# ---------------------------------------------------------------- foto

def converti_foto(sorgente: Path, destinazione: Path, qualita: int) -> None:
    with Image.open(sorgente) as img:
        exif = img.info.get("exif")
        img = ImageOps.exif_transpose(img)  # mantiene l'orientamento corretto
        img = img.convert("RGB")
        opzioni = {"quality": qualita}
        if exif:
            opzioni["exif"] = exif
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        img.save(destinazione, "JPEG", **opzioni)


# ---------------------------------------------------------------- video

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def info_video(file: Path) -> tuple[str | None, str | None]:
    """Restituisce (codec video, tipo HDR oppure None)."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(file)],
                       capture_output=True, text=True, errors="replace")
    riga = re.search(r"Stream #.*?Video: (.*)", r.stderr)
    if not riga:
        return None, None
    testo = riga.group(1)
    codec = testo.split()[0].strip(",")
    hdr = None
    if "arib-std-b67" in testo:      # HLG: quello dei video iPhone
        hdr = "arib-std-b67"
    elif "smpte2084" in testo:       # PQ / HDR10
        hdr = "smpte2084"
    elif "bt2020" in testo:
        hdr = "arib-std-b67"
    return codec, hdr


def converti_video(sorgente: Path, destinazione: Path, crf: int, hdr: str | None) -> None:
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    temporaneo = destinazione.with_name(destinazione.stem + ".parziale.mp4")

    def esegui(con_filtro_hdr: bool) -> int:
        livello = "quiet" if con_filtro_hdr else "error"
        cmd = [FFMPEG, "-hide_banner", "-loglevel", livello, "-stats", "-y",
               "-i", str(sorgente),
               "-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0"]
        if con_filtro_hdr:
            cmd += ["-vf", filtro_hdr(hdr)]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", str(temporaneo)]
        return subprocess.run(cmd).returncode

    try:
        codice = esegui(hdr is not None)
        if codice != 0 and hdr:
            print("\n    Correzione colori HDR non riuscita, riprovo senza...")
            codice = esegui(False)
        if codice != 0:
            raise RuntimeError("ffmpeg non è riuscito a convertire il video")
        temporaneo.replace(destinazione)
    finally:
        if temporaneo.exists():
            temporaneo.unlink()


# ---------------------------------------------------------------- logica comune

def trova_file(cartella: Path, estensioni: set, ricorsivo: bool) -> list[Path]:
    pattern = "**/*" if ricorsivo else "*"
    return sorted(f for f in cartella.glob(pattern)
                  if f.is_file() and f.suffix.lower() in estensioni
                  and ".parziale." not in f.name)


def percorso_uscita(f: Path, args, estensione: str) -> Path:
    out = args.destinazione / f.relative_to(args.origine).with_suffix(estensione)
    if out.resolve() == f.resolve():  # evita di sovrascrivere l'originale
        out = out.with_name(out.stem + "_convertito" + estensione)
    return out


def esegui_foto(args) -> tuple[int, int, int]:
    files = trova_file(args.origine, EST_FOTO, args.ricorsivo)
    print(f"\n--- FOTO: {len(files)} file HEIC trovati ---")
    ok = saltati = errori = 0
    for i, f in enumerate(files, 1):
        out = percorso_uscita(f, args, ".jpg")
        nome = out.relative_to(args.destinazione)
        if out.exists() and not args.sovrascrivi:
            print(f"[{i}/{len(files)}] Già presente, salto: {nome}")
            saltati += 1
            continue
        try:
            converti_foto(f, out, args.qualita)
            print(f"[{i}/{len(files)}] OK: {f.name} -> {nome}")
            ok += 1
        except Exception as e:
            print(f"[{i}/{len(files)}] ERRORE su {f.name}: {e}")
            errori += 1
    return ok, saltati, errori


def esegui_video(args) -> tuple[int, int, int]:
    files = trova_file(args.origine, EST_VIDEO, args.ricorsivo)
    print(f"\n--- VIDEO: {len(files)} file video trovati ---")
    crf = QUALITA_VIDEO[args.qualita_video]
    ok = saltati = errori = 0
    for i, f in enumerate(files, 1):
        out = percorso_uscita(f, args, ".mp4")
        nome = out.relative_to(args.destinazione)
        if out.exists() and not args.sovrascrivi:
            print(f"[{i}/{len(files)}] Già presente, salto: {nome}")
            saltati += 1
            continue
        codec, hdr = info_video(f)
        if codec != "hevc":
            print(f"[{i}/{len(files)}] Non è HEVC ({codec or 'sconosciuto'}), salto: {f.name}")
            saltati += 1
            continue
        print(f"[{i}/{len(files)}] Converto {f.name}{' (HDR)' if hdr else ''}... "
              "può richiedere qualche minuto")
        try:
            converti_video(f, out, crf, hdr)
            print(f"    OK -> {nome}")
            ok += 1
        except Exception as e:
            print(f"    ERRORE: {e}")
            errori += 1
    return ok, saltati, errori


def converti(args) -> int:
    totale = [0, 0, 0]
    if args.tipo in ("foto", "tutto"):
        totale = [a + b for a, b in zip(totale, esegui_foto(args))]
    if args.tipo in ("video", "tutto"):
        totale = [a + b for a, b in zip(totale, esegui_video(args))]
    ok, saltati, errori = totale
    print(f"\nFatto. Convertiti: {ok}  Saltati: {saltati}  Errori: {errori}")
    return 1 if errori else 0


# ---------------------------------------------------------------- menu interattivo

def chiedi_cartella(domanda: str, deve_esistere: bool) -> Path:
    while True:
        testo = input(domanda).strip().strip('"').strip("'").strip()
        if testo.startswith("& "):  # PowerShell aggiunge "& " quando trascini
            testo = testo[2:].strip().strip('"').strip("'")
        if not testo:
            print("  Scrivi un percorso (puoi anche trascinare qui la cartella).")
            continue
        cartella = Path(testo).expanduser()
        if deve_esistere and not cartella.is_dir():
            print(f"  La cartella '{cartella}' non esiste, riprova.")
            continue
        return cartella


def chiedi_si_no(domanda: str, default: bool) -> bool:
    suffisso = " [S/n]: " if default else " [s/N]: "
    while True:
        r = input(domanda + suffisso).strip().lower()
        if not r:
            return default
        if r in ("s", "si", "sì", "y", "yes"):
            return True
        if r in ("n", "no"):
            return False
        print("  Rispondi s oppure n.")


def chiedi_scelta(domanda: str, opzioni: list[tuple[str, str]], default: str) -> str:
    """opzioni = [(tasto, descrizione), ...]; restituisce il tasto scelto."""
    print(domanda)
    for tasto, descr in opzioni:
        print(f"  {tasto}) {descr}")
    validi = {t for t, _ in opzioni}
    while True:
        r = input(f"Scelta [{default}]: ").strip() or default
        if r in validi:
            return r
        print("  Scelta non valida, riprova.")


def chiedi_qualita(default: int = 90) -> int:
    while True:
        r = input(f"Qualità JPG da 1 a 100 [{default}]: ").strip()
        if not r:
            return default
        if r.isdigit() and 1 <= int(r) <= 100:
            return int(r)
        print("  Inserisci un numero tra 1 e 100.")


def modalita_interattiva() -> int:
    while True:
        print("\n" + "=" * 44)
        print("   CONVERTITORE FOTO E VIDEO iPHONE")
        print("=" * 44)
        print("(Premi Invio per accettare il valore tra parentesi)\n")

        tipo = chiedi_scelta("Cosa vuoi convertire?", [
            ("1", "Foto  HEIC -> JPG"),
            ("2", "Video HEVC -> MP4"),
            ("3", "Foto e video"),
            ("0", "Esci"),
        ], "3")
        if tipo == "0":
            return 0
        tipo = {"1": "foto", "2": "video", "3": "tutto"}[tipo]

        print()
        origine = chiedi_cartella("Cartella di ORIGINE: ", deve_esistere=True)
        destinazione = chiedi_cartella("Cartella di DESTINAZIONE: ", deve_esistere=False)
        print()

        qualita = 90
        qualita_video = "media"
        if tipo in ("foto", "tutto"):
            qualita = chiedi_qualita()
        if tipo in ("video", "tutto"):
            qualita_video = {"1": "alta", "2": "media", "3": "bassa"}[chiedi_scelta(
                "Qualità video:", [
                    ("1", "Alta  (file più grandi)"),
                    ("2", "Media (consigliata)"),
                    ("3", "Bassa (file più piccoli)"),
                ], "2")]
        ricorsivo = chiedi_si_no("Includere le sottocartelle?", False)
        sovrascrivi = chiedi_si_no("Sovrascrivere i file già convertiti?", False)

        print("\nRiepilogo:")
        print(f"  Cosa:          {'foto e video' if tipo == 'tutto' else tipo}")
        print(f"  Origine:       {origine}")
        print(f"  Destinazione:  {destinazione}")
        if tipo in ("foto", "tutto"):
            print(f"  Qualità JPG:   {qualita}")
        if tipo in ("video", "tutto"):
            print(f"  Qualità video: {qualita_video}")
        print(f"  Sottocartelle: {'sì' if ricorsivo else 'no'}")
        print(f"  Sovrascrivi:   {'sì' if sovrascrivi else 'no'}\n")

        if chiedi_si_no("Avviare la conversione?", True):
            converti(argparse.Namespace(
                tipo=tipo, origine=origine, destinazione=destinazione,
                qualita=qualita, qualita_video=qualita_video,
                ricorsivo=ricorsivo, sovrascrivi=sovrascrivi))
        else:
            print("Annullato.")

        if not chiedi_si_no("\nVuoi fare un'altra conversione?", False):
            return 0


# ---------------------------------------------------------------- avvio

def main() -> int:
    if len(sys.argv) == 1:
        try:
            return modalita_interattiva()
        except (KeyboardInterrupt, EOFError):
            print("\nInterrotto.")
            return 1

    p = argparse.ArgumentParser(description="Converte foto HEIC in JPG e video HEVC in MP4.")
    p.add_argument("origine", type=Path, help="Cartella con le foto/video da convertire")
    p.add_argument("destinazione", type=Path, help="Cartella dove salvare i file convertiti")
    p.add_argument("--tipo", choices=["foto", "video", "tutto"], default="tutto")
    p.add_argument("--qualita", type=int, default=90, help="Qualità JPG 1-100 (default 90)")
    p.add_argument("--qualita-video", choices=list(QUALITA_VIDEO), default="media")
    p.add_argument("--ricorsivo", action="store_true", help="Cerca anche nelle sottocartelle")
    p.add_argument("--sovrascrivi", action="store_true", help="Riconverte i file già presenti")
    args = p.parse_args()

    if not args.origine.is_dir():
        print(f"Errore: la cartella '{args.origine}' non esiste.")
        return 1
    if not 1 <= args.qualita <= 100:
        print("Errore: --qualita deve essere tra 1 e 100.")
        return 1
    try:
        return converti(args)
    except KeyboardInterrupt:
        print("\nInterrotto.")
        return 1


if __name__ == "__main__":
    codice = main()
    if len(sys.argv) == 1:
        input("\nPremi Invio per chiudere...")
    sys.exit(codice)
