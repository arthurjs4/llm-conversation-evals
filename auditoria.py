"""
Auditoria: reclassifica TODAS as conversas salvas e mostra o que mudaria no registro de leads.

Uso:
    python auditoria.py                          -> só mostra o que mudaria (nada é gravado)
    python auditoria.py --gravar                 -> atualiza dados/leads.json
    python auditoria.py --so 15550100101,...     -> só esses telefones
    python auditoria.py --classificador llm      -> usa IA em vez das regras

Gera um relatório em dados/auditoria_AAAA-MM-DD_HHMM.md
"""
import argparse
import json
import os
import sys
from datetime import datetime

from evals.classificador import escolher

sys.stdout.reconfigure(encoding="utf-8")

PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
PASTA_CONVERSAS = os.path.join(PASTA_DADOS, "conversas")
ARQ_LEADS = os.path.join(PASTA_DADOS, "leads.json")


def carregar_leads() -> dict:
    try:
        with open(ARQ_LEADS, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--so", default="")
    ap.add_argument("--classificador", choices=["regras", "llm"], default="regras")
    args = ap.parse_args()
    so = {x for x in args.so.split(",") if x}
    clf = escolher(args.classificador)
    leads = carregar_leads()

    linhas = []
    for arq in sorted(os.listdir(PASTA_CONVERSAS)):
        tel = arq[:-5]
        if so and tel not in so:
            continue
        with open(os.path.join(PASTA_CONVERSAS, arq), encoding="utf-8") as f:
            msgs = json.load(f)
        if not msgs:
            continue
        lead = leads.get(tel, {})
        antes = lead.get("estagio") or "-"
        depois = clf.classificar(msgs)
        linhas.append({"tel": tel, "empresa": lead.get("empresa", ""), "antes": antes, "depois": depois})
        marca = "  " if antes == depois else "→ "
        print(f"{marca}{tel:14} {lead.get('empresa', '')[:24]:24} {antes:20} → {depois}")
        if args.gravar and tel in leads:
            leads[tel]["estagio"] = depois

    mudaram = [r for r in linhas if r["antes"] != r["depois"]]
    agora = datetime.now()
    rel = [f"# Auditoria · {agora:%d/%m/%Y %H:%M}", "",
           f"{'Gravado' if args.gravar else 'Simulação (nada gravado)'} · {len(linhas)} conversas · "
           f"{len(mudaram)} mudam de estágio", "",
           "| Empresa | Telefone | Antes | Depois |", "|---|---|---|---|"]
    for r in sorted(linhas, key=lambda x: (x["antes"] == x["depois"], x["depois"])):
        neg = "**" if r["antes"] != r["depois"] else ""
        rel.append(f"| {r['empresa']} | {r['tel']} | {r['antes']} | {neg}{r['depois']}{neg} |")
    caminho = os.path.join(PASTA_DADOS, f"auditoria_{agora:%Y-%m-%d_%H%M}{'' if args.gravar else '_simulacao'}.md")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(rel) + "\n")
    if args.gravar:
        with open(ARQ_LEADS, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=1)
    print(f"\n{len(mudaram)} de {len(linhas)} mudam de estágio. Relatório: {caminho}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
