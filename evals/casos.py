"""Conversas SINTÉTICAS (nomes e empresas inventados) no formato conversa -> estágio esperado.

Cada fala é (dias_atrás, quem, texto): quem = 'a' (agência/vendedor) ou 'c' (cliente/lead).
"""
import time

DIA = 86400
AGORA = time.time()

PROSPECCAO = ("Boa tarde! Aqui é o Bruno. Vi uma avaliação agradecendo à Carla pelo atendimento na Contabil Exemplo. "
              "Eu monto anúncios para escritórios de contabilidade: quando alguém pesquisa os serviços de vocês em "
              "Cidade Exemplo, o anúncio aparece e leva direto para o WhatsApp. Posso gravar um vídeo de 4 minutos "
              "mostrando o que aparece hoje quando alguém procura contador na cidade?")
FU1 = "Oi! Passando para ver se você viu minha mensagem. Posso gravar o vídeo para vocês?"
FU2 = "Última mensagem por aqui: se quiser o vídeo mostrando o que aparece no Google, é só me falar!"


def conversa(*falas):
    return [{"de": "agencia" if q == "a" else "cliente", "texto": t, "quando": int(AGORA - d * DIA)} for d, q, t in falas]


# (nome do caso, conversa, estágio esperado)
CASOS = [
    ("só a prospecção, ontem", conversa((1, "a", PROSPECCAO)), "PROSPECCAO"),
    ("prospecção + follow-up 1", conversa((3, "a", PROSPECCAO), (1, "a", FU1)), "FOLLOWUP"),
    ("2 follow-ups e 2 dias sem resposta", conversa((7, "a", PROSPECCAO), (5, "a", FU1), (3, "a", FU2)), "PERDIDO"),
    ("aceitou o vídeo na 1ª mensagem", conversa((0.2, "a", PROSPECCAO), (0.1, "c", "Pode gravar sim, obrigada!")), "VIDEO_ACEITO"),
    ("aceitou depois do follow-up 1", conversa((3, "a", PROSPECCAO), (1, "a", FU1), (0.5, "c", "Opa, desculpa a demora. Pode mandar o vídeo")), "VIDEO_ACEITO"),
    ("aceitou em inglês", conversa((1, "a", PROSPECCAO), (0.5, "c", "Sure, send me the video!")), "VIDEO_ACEITO"),
    ("vídeo enviado", conversa((2, "a", PROSPECCAO), (1.5, "c", "pode sim"), (0.5, "a", "Carla, segue o vídeo: https://www.loom.com/share/abc123")), "VIDEO_ENVIADO"),
    ("viu o vídeo e marcou reunião", conversa((3, "a", PROSPECCAO), (2.5, "c", "pode mandar"), (2, "a", "Segue: loom.com/share/x1"),
                                             (1, "c", "Vi o vídeo, muito bom. Vamos conversar?"), (0.9, "a", "Claro! Quinta às 14h funciona?"),
                                             (0.8, "c", "Fechado, quinta 14h")), "REUNIAO_AGENDADA"),
    ("só resposta automática", conversa((1, "a", PROSPECCAO), (1, "c", "Olá! No momento não estamos disponíveis. Retornaremos em breve.")), "PROSPECCAO"),
    ("recusou", conversa((1, "a", PROSPECCAO), (0.5, "c", "Obrigada, mas não temos interesse no momento.")), "PERDIDO"),
    ("lead que chamou primeiro", conversa((0.1, "c", "Olá, vi o anúncio de vocês")), "EM_CONVERSA"),
    ("respondeu sem pedir o vídeo", conversa((1, "a", PROSPECCAO), (0.5, "c", "Quem é você? Como conseguiu meu número?")), "EM_CONVERSA"),
    ("fechou na reunião", conversa((5, "a", PROSPECCAO), (4, "c", "pode mandar"), (3, "a", "loom.com/share/zz"),
                                   (2, "a", "Foi ótima a reunião de hoje! Segue o link de pagamento do primeiro mês."),
                                   (1, "c", "Pago! Quando começamos?")), "FECHADO_GANHO"),
    # ---- armadilhas clássicas que um classificador ingênuo erra
    ("robô de atendimento respondeu", conversa((1, "a", PROSPECCAO), (0.9999, "c", "Thanks for reaching out! I'll ask a "
     "representative to respond. Someone will be with you shortly!")), "PROSPECCAO"),
    ("cardápio automático", conversa((1, "a", PROSPECCAO), (0.99998, "c", "Café Exemplo thanks for contacting us. In order "
     "to send you a quote we will need some information. Which menu would you like a quote for? Opening hours: Monday - "
     "Friday 9am to 8pm")), "PROSPECCAO"),
    ("'Oi Ok' depois de 'Posso mandar?'", conversa((2, "a", "Diego, boa tarde! Vi uma avaliação da Padaria Exemplo. Gravei "
     "um vídeo rápido mostrando como colocar esse resultado na frente de quem procura no Google. Posso mandar?"),
                                                  (1.9, "c", "Oi\nOk")), "VIDEO_ACEITO"),
    ("3 toques e só 'Obrigado'", conversa((23, "a", PROSPECCAO), (14, "a", FU1),
                                          (8, "a", "Boa tarde! Última mensagem, prometo. Fica uma dica de graça..."),
                                          (7.99, "c", "Obrigado")), "PERDIDO"),
    ("vai falar com a sócia", conversa((22, "a", PROSPECCAO), (21.9, "c", "Vocês gravam o conteúdo?"),
                                       (21.8, "a", "Não, cuidamos do perfil do Google e dos anúncios."),
                                       (21.7, "c", "Eu posso comunicar com a Marta, se ela aprovar eu te mando o contato dela"),
                                       (21.69, "a", "Claro! Seria de muita ajuda!"), (21.68, "c", "Beleza 👍"),
                                       (21.67, "a", "Top, muito obrigado!")), "AGUARDANDO_RETORNO"),
    ("proposta por escrito + 'vamos analisar'", conversa((1, "a", PROSPECCAO), (0.5, "c", "Pode enviar uma proposta por "
     "escrito para nossa gerente avaliar?"), (0.4, "a", "[documento] Aqui está nossa proposta com os valores."),
                                                         (0.3, "c", "Perfeito, nossa gerente irá analisar e te retornamos"),
                                                         (0.29, "c", "Obrigada")), "PROPOSTA"),
    ("encaminhou para o setor responsável", conversa((2, "a", PROSPECCAO), (1.5, "c", "Vou encaminhar sua mensagem para o "
     "setor responsável. Assim que possível te daremos um retorno")), "AGUARDANDO_RETORNO"),
]
