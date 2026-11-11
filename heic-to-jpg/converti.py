#!/usr/bin/env python3
"""Converte tutte le foto HEIC/HEIF di una cartella in JPG.

Uso:
    python converti.py                (modalità interattiva: fa le domande)
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


def chiedi_cartella(domanda: str, deve_esistere: bool) -> Path:
    while True:
        testo = input(domanda).strip().strip('"').strip("'").strip()
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


def chiedi_qualita(default: int = 90) -> int:
    while True:
        r = input(f"Qualità JPG da 1 a 100 [{default}]: ").strip()
        if not r:
            return default
        if r.isdigit() and 1 <= int(r) <= 100:
            return int(r)
        print("  Inserisci un numero tra 1 e 100.")


def modalita_interattiva() -> argparse.Namespace:
    print("=" * 40)
    print("   CONVERTITORE HEIC -> JPG")
    print("=" * 40)
    print("(Premi Invio per accettare il valore tra parentesi)\n")
    origine = chiedi_cartella("Cartella di ORIGINE (foto HEIC): ", deve_esistere=True)
    destinazione = chiedi_cartella("Cartella di DESTINAZIONE (JPG): ", deve_esistere=False)
    qualita = chiedi_qualita()
    ricorsivo = chiedi_si_no("Includere le sottocartelle?", False)
    sovrascrivi = chiedi_si_no("Sovrascrivere i JPG già esistenti?", False)

    print("\nRiepilogo:")
    print(f"  Origine:       {origine}")
    print(f"  Destinazione:  {destinazione}")
    print(f"  Qualità:       {qualita}")
    print(f"  Sottocartelle: {'sì' if ricorsivo else 'no'}")
    print(f"  Sovrascrivi:   {'sì' if sovrascrivi else 'no'}\n")
    if not chiedi_si_no("Avviare la conversione?", True):
        print("Annullato.")
        sys.exit(0)
    print()
    return argparse.Namespace(origine=origine, destinazione=destinazione,
                              qualita=qualita, ricorsivo=ricorsivo,
                              sovrascrivi=sovrascrivi)


def main() -> int:
    p = argparse.ArgumentParser(description="Converte foto HEIC in JPG.")
    p.add_argument("origine", type=Path, help="Cartella con le foto HEIC")
    p.add_argument("destinazione", type=Path, help="Cartella dove salvare i JPG")
    p.add_argument("--qualita", type=int, default=90, help="Qualità JPG 1-100 (default 90)")
    p.add_argument("--ricorsivo", action="store_true", help="Cerca anche nelle sottocartelle")
    p.add_argument("--sovrascrivi", action="store_true", help="Sovrascrive i JPG già esistenti")
    if len(sys.argv) == 1:
        try:
            args = modalita_interattiva()
        except (KeyboardInterrupt, EOFError):
            print("\nAnnullato.")
            return 1
    else:
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
    codice = main()
    if len(sys.argv) == 1:
        input("\nPremi Invio per chiudere...")
    sys.exit(codice)
