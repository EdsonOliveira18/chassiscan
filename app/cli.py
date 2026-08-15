import argparse
import json
import sys

import cv2

from .ocr_engine import read_vin


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chassiscan", description="Lê o VIN de uma foto.")
    parser.add_argument("imagem", help="caminho da foto do chassi")
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    args = parser.parse_args(argv)

    img = cv2.imread(args.imagem)
    if img is None:
        print(f"Erro: não foi possível abrir '{args.imagem}'", file=sys.stderr)
        return 1

    result = read_vin(img)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False))
    else:
        status = "VÁLIDO" if result.valid else "NÃO VALIDADO"
        print(f"VIN: {result.vin or '-'}  [{status}]")
        print(
            f"Confiança: {result.confidence:.2f} | "
            f"variante={result.variant} rotação={result.rotation}"
        )
        if not result.valid and result.candidates:
            print("Candidatos:", ", ".join(result.candidates))
    return 0 if result.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
