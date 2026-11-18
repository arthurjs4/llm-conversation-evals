# llm-conversation-evals

Suíte de avaliação (evals) para um **classificador de conversas de vendas**: dado um histórico de WhatsApp, em qual estágio do funil o lead está? Serve para testar mudanças de prompt ou de modelo sem medo de regressão, e para **auditar** um conjunto inteiro de conversas salvas.

Tudo aqui é **sintético**: nomes, empresas e telefones são inventados (números 555).

## Formato: conversa → estágio esperado

```python
# evals/casos.py
("aceitou o vídeo na 1ª mensagem",
 conversa((0.2, "a", PROSPECCAO), (0.1, "c", "Pode gravar sim, obrigada!")),
 "VIDEO_ACEITO")
```

Cada fala é `(dias_atrás, quem, texto)`, com `a` = vendedor e `c` = cliente. Os 20 casos incluem as **armadilhas** que classificadores ingênuos erram:

- resposta automática de robô (não conta como resposta do lead);
- "Oi, ok" logo depois de "Posso mandar?" (é um aceite);
- três toques sem resposta e só um "Obrigado" no fim (lead perdido);
- "vou falar com minha sócia" (a vez é do lead, não é recusa);
- proposta por escrito + "vamos analisar" (estágio de proposta).

## Uso

```bash
pip install -r requirements.txt

python avaliar_ia.py                         # classificador de regras, offline (linha de base)
python avaliar_ia.py --classificador llm     # Claude (ANTHROPIC_API_KEY) ou Ollama local
python avaliar_ia.py --minimo 0.9            # sai com código 1 se acertar menos de 90% (bom para CI)
```

Saída:

```
OK só a prospecção, ontem                   -> PROSPECCAO          (esperado PROSPECCAO)
XX vai falar com a sócia                    -> EM_CONVERSA         (esperado AGUARDANDO_RETORNO)
19/20 corretos (95%)
```

## Auditoria de conversas salvas

`auditoria.py` reclassifica todas as conversas de `dados/conversas/*.json` e compara com o estágio guardado em `dados/leads.json`:

```bash
python auditoria.py            # simulação, só mostra o que mudaria
python auditoria.py --gravar   # atualiza dados/leads.json
```

Gera um relatório em Markdown (`dados/auditoria_*.md`) com a tabela antes → depois.

## Trocando o classificador

Qualquer objeto com `classificar(msgs: list[dict]) -> str` serve (veja `evals/classificador.py`). Basta registrá-lo em `escolher()` e rodar os mesmos casos.

## Licença

MIT
