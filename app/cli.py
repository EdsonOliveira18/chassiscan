"""CLI do ChassiScan: le o VIN de uma foto."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

from . import __service__, __version__
from .image_utils import decode_bytes
from .ocr_engine import read_vin

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOT_VALIDATED = 2
EXIT_INTERRUPTED = 130


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=__service__, description="Le o VIN (chassi) de uma foto.")
    parser.add_argument("imagem", help="caminho da foto do chassi")
    parser.add_argument("--json", action="store_true", help="saida em JSON")
    parser.add_argument("-q", "--quiet", action="store_true", help="silencia logs")
    parser.add_argument("--version", action="version", version=f"{__service__} {__version__}")
    return parser


def load_image(path: Path) -> np.ndarray | None:
    """Le via bytes + imdecode: suporta caminhos com acentos/unicode (Windows)."""
    try:
        return decode_bytes(path.read_bytes())
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.ERROR if args.quiet else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    path = Path(args.imagem)
    if not path.is_file():
        print(f"Erro: arquivo nao encontrado: '{path}'", file=sys.stderr)
        return EXIT_ERROR

    img = load_image(path)
    if img is None:
        print(f"Erro: nao foi possivel abrir/decodificar '{path}'", file=sys.stderr)
        return EXIT_ERROR

    try:
        result = read_vin(img)
    except KeyboardInterrupt:
        print("Interrompido.", file=sys.stderr)
        return EXIT_INTERRUPTED
    except Exception as exc:
        print(f"Erro inesperado no OCR: {exc}", file=sys.stderr)
        logging.debug("stacktrace", exc_info=True)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False))
    else:
        status = "VALIDO" if result.valid else "NAO VALIDADO"
        print(f"VIN: {result.vin or '-'}  [{status}]")
        print(
            f"Confianca: {result.confidence:.2f} | "
            f"variante={result.variant} rotacao={result.rotation}"
        )
        if not result.valid and result.candidates:
            print("Candidatos:", ", ".join(result.candidates))

    return EXIT_OK if result.valid else EXIT_NOT_VALIDATED


if __name__ == "__main__":
    raise SystemExit(main())
