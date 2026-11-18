"""Classificadores de estágio do funil. Qualquer objeto com `classificar(msgs) -> str` serve.

- ClassificadorRegras: heurísticas offline (rápido, sem IA), linha de base.
- ClassificadorLLM: pede o estágio a uma IA (Claude se houver ANTHROPIC_API_KEY, senão Ollama).
"""
import json
import os
import re
import time

import requests

ESTAGIOS = ["PROSPECCAO", "FOLLOWUP", "EM_CONVERSA", "VIDEO_ACEITO", "VIDEO_ENVIADO", "AGUARDANDO_RETORNO",
            "REUNIAO_AGENDADA", "PROPOSTA", "FECHADO_GANHO", "PERDIDO"]

AUTOMATICA = re.compile(r"no momento n[ãa]o estamos|retornaremos em breve|thanks for (reaching out|contacting)|"
                        r"representative to respond|in order to send you|opening hours|mensagem autom[áa]tica", re.I)
RECUSA = re.compile(r"n[ãa]o (temos|tenho) interesse|not interested|n[ãa]o precisamos", re.I)
LINK_VIDEO = re.compile(r"loom\.com/", re.I)
PAGO = re.compile(r"\bpago\b|paguei|pagamento feito|assinei|payment (done|made)", re.I)
ACEITE = re.compile(r"^((oi|ol[aá]|opa|bom dia|boa tarde)[\s,!]*)*(ok(ay)?|sim|pode( sim| mandar| gravar)?|claro|quero|manda|yes|sure)\b"
                    r"|pode (gravar|mandar)|send me|sure", re.I)
ESPERA = re.compile(r"encaminhar|vou (analisar|ver)|ir[áa] analisar|comunicar com|falar com (o|a|meu|minha)|te retornamos|"
                    r"te retorno", re.I)
CORTESIA = re.compile(r"^(muito )?(obrigad[oa]|valeu|thanks|beleza|ok)[\s!.👍]*$", re.I)
DIA = 86400


class ClassificadorRegras:
    def classificar(self, msgs: list[dict]) -> str:
        reais = [m for m in msgs if not (m["de"] == "cliente" and AUTOMATICA.search(m["texto"]))]
        ag = [m for m in reais if m["de"] == "agencia"]
        cl = [m for m in reais if m["de"] == "cliente"]
        agora = time.time()
        txt_cl = " ".join(m["texto"] for m in cl)
        if cl and PAGO.search(txt_cl) and any("pagamento" in m["texto"].lower() for m in ag):
            return "FECHADO_GANHO"
        if cl and RECUSA.search(txt_cl):
            return "PERDIDO"
        if not ag:
            return "EM_CONVERSA"
        if cl and any("[documento]" in m["texto"] or "proposta" in m["texto"].lower() for m in ag) and ESPERA.search(txt_cl):
            return "PROPOSTA"
        enviou_video = any(LINK_VIDEO.search(m["texto"]) for m in ag)
        if enviou_video:
            apos = [m for m in cl if m["quando"] > max(a["quando"] for a in ag if LINK_VIDEO.search(a["texto"]))]
            ofereceu_hora = any(re.search(r"\b\d{1,2}h\b|às \d", m["texto"]) for m in ag)
            if apos and ofereceu_hora and re.search(r"fechado|combinado|confirmado|\b\d{1,2}h\b", apos[-1]["texto"], re.I):
                return "REUNIAO_AGENDADA"
            return "VIDEO_ENVIADO"
        if cl:
            if ESPERA.search(txt_cl):
                return "AGUARDANDO_RETORNO"
            ultimo = cl[-1]["texto"].strip()
            if len(ag) >= 3 and CORTESIA.match(ultimo):
                return "PERDIDO"
            if ACEITE.search(ultimo) and not ultimo.endswith("?"):
                return "VIDEO_ACEITO"
            return "EM_CONVERSA"
        # só mensagens da agência
        if len(ag) >= 3 and agora - ag[-1]["quando"] > 2 * DIA - 1:
            return "PERDIDO"
        return "PROSPECCAO" if len(ag) <= 1 else "FOLLOWUP"


class ClassificadorLLM:
    """Pede o estágio à IA. Exige ANTHROPIC_API_KEY ou um Ollama rodando."""

    def __init__(self):
        self.modelo = os.environ.get("CLAUDE_MODELO", "claude-sonnet-5-5")
        self.ollama = os.environ.get("OLLAMA_MODEL", "qwen3:14b")

    def _prompt(self, msgs):
        conv = "\n".join(f"{'VENDEDOR' if m['de'] == 'agencia' else 'LEAD'}: {m['texto']}" for m in msgs)
        return ("Classifique em que estágio do funil está esta conversa de vendas por WhatsApp. Respostas automáticas "
                "de robô não contam como resposta do lead. Estágios possíveis: " + ", ".join(ESTAGIOS) +
                '.\nResponda só JSON: {"estagio": "..."}\n\n' + conv)

    def classificar(self, msgs: list[dict]) -> str:
        p = self._prompt(msgs)
        if os.environ.get("ANTHROPIC_API_KEY"):
            import anthropic
            r = anthropic.Anthropic().messages.create(model=self.modelo, max_tokens=200,
                                                      messages=[{"role": "user", "content": p}])
            txt = "".join(b.text for b in r.content if b.type == "text")
        else:
            r = requests.post("http://localhost:11434/api/generate", timeout=300,
                              json={"model": self.ollama, "prompt": p, "stream": False, "format": "json",
                                    "options": {"temperature": 0}})
            r.raise_for_status()
            txt = r.json().get("response", "")
        try:
            return json.loads(txt[txt.find("{"):txt.rfind("}") + 1]).get("estagio", "FALHOU")
        except json.JSONDecodeError:
            return "FALHOU"


def escolher(nome: str):
    return ClassificadorLLM() if nome == "llm" else ClassificadorRegras()
