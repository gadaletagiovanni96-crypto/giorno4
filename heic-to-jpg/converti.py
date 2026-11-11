#!/usr/bin/env python3
"""Converte tutte le foto HEIC/HEIF di una cartella in JPG.

Uso:
    python converti.py CARTELLA_ORIGINE CARTELLA_DESTINAZIONE [--qualita 90] [--ricorsivo] [--sovrascrivi]
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
    from pillow_heif import register_heif_opener
except ImportError:
    sys.exit("Librerie mancanti. Esegui prima:  pip install -r requirements.txt")

register_heif_opener()

ESTENSIONI = {".heic", ".heif"}


def converti_file(sorgente: Path, destinazione: Path, qualita: int) -> None:
    with Image.open(sorgente) as img:
        exif = img.info.get("exif")
        img = ImageOps.exif_transpose(img)  # mantiene l'orientamento corretto
        img = img.convert("RGB")
        opzioni = {"quality": qualita}
        if exif:
            opzioni["exif"] = exif
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        img.save(destinazione, "JPEG", **opzioni)


def main() -> int:
    p = argparse.ArgumentParser(description="Converte foto HEIC in JPG.")
    p.add_argument("origine", type=Path, help="Cartella con le foto HEIC")
    p.add_argument("destinazione", type=Path, help="Cartella dove salvare i JPG")
    p.add_argument("--qualita", type=int, default=90, help="Qualità JPG 1-100 (default 90)")
    p.add_argument("--ricorsivo", action="store_true", help="Cerca anche nelle sottocartelle")
    p.add_argument("--sovrascrivi", action="store_true", help="Sovrascrive i JPG già esistenti")
    args = p.parse_args()

    if not args.origine.is_dir():
        print(f"Errore: la cartella '{args.origine}' non esiste.")
        return 1

    pattern = "**/*" if args.ricorsivo else "*"
    files = sorted(f for f in args.origine.glob(pattern)
                   if f.is_file() and f.suffix.lower() in ESTENSIONI)
    if not files:
        print("Nessun file HEIC trovato.")
        return 0

    ok = saltati = errori = 0
    for i, f in enumerate(files, 1):
        relativo = f.relative_to(args.origine).with_suffix(".jpg")
        out = args.destinazione / relativo
        if out.exists() and not args.sovrascrivi:
            print(f"[{i}/{len(files)}] Già presente, salto: {relativo}")
            saltati += 1
            continue
        try:
            converti_file(f, out, args.qualita)
            print(f"[{i}/{len(files)}] OK: {f.name} -> {relativo}")
            ok += 1
        except Exception as e:
            print(f"[{i}/{len(files)}] ERRORE su {f.name}: {e}")
            errori += 1

    print(f"\nFatto. Convertiti: {ok}  Saltati: {saltati}  Errori: {errori}")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
