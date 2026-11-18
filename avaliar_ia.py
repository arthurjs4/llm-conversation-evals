"""
Teste de qualidade do classificador: conversas sintéticas e o estágio esperado.
Rode depois de qualquer mudança no prompt ou no modelo:

    python avaliar_ia.py                       # classificador de regras (offline)
    python avaliar_ia.py --classificador llm   # usa Claude/Ollama
    python avaliar_ia.py --minimo 0.9          # exit 1 se a taxa de acerto ficar abaixo de 90%
"""
import argparse
import sys
import time

from evals.casos import CASOS
from evals.classificador import escolher

sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classificador", choices=["regras", "llm"], default="regras")
    ap.add_argument("--minimo", type=float, default=1.0, help="taxa mínima de acerto (0 a 1)")
    args = ap.parse_args()
    clf = escolher(args.classificador)
    acertos = 0
    for nome, msgs, esperado in CASOS:
        t = time.time()
        try:
            obtido = clf.classificar(msgs)
        except Exception as e:  # noqa: BLE001
            obtido = f"ERRO:{type(e).__name__}"
        ok = obtido == esperado
        acertos += ok
        print(f"{'OK' if ok else 'XX'} {nome:42} -> {obtido:19} (esperado {esperado:19}) {time.time() - t:5.1f}s")
    taxa = acertos / len(CASOS)
    print(f"\n{acertos}/{len(CASOS)} corretos ({taxa:.0%})")
    return 0 if taxa >= args.minimo else 1


if __name__ == "__main__":
    sys.exit(main())
