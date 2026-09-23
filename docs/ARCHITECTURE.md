# Arquitetura

```text
WhatsApp → Meta → HTTPS/túnel → webhook HMAC → inbox SQLite
                                               ↓ worker único
                                     conversa e sessão SQLite
                                               ↓ confirmação
                                     subprocesso fli (55s)
                                               ↓
                                     normalização e ranking
                                               ↓
                                     WhatsApp Graph API
```

`webhook.py` valida desafio, assinatura e tamanho; confirma eventos após persistência. `messaging.py` filtra remetente/idade, deduplica, processa e envia. `conversation.py` mantém passos com busca injetável. `flights.py` resolve aeroportos, limita execução e apresenta resultados. `providers/google_flights.py` isola a biblioteca não oficial.

A transação SQLite é liberada antes da consulta. No reinício, itens `processing` voltam à fila; `sending` vira `uncertain`, evitando repetir envios possivelmente entregues. Não existe garantia de entrega exatamente uma vez. Worker único: cancelamentos aguardam a busca em andamento.

Normalização exige ida/volta completas, datas/aeroportos correspondentes, BRL e preço positivo. No fli, o preço da primeira jornada representa a ida e volta: não se somam as jornadas. Ranking remove duplicatas, limita a quatro e não promete cobrir o mercado. Maior preço ordena somente as opções encontradas.

Credenciais em `.env`; conversas/ofertas em SQLite local. Logs omitem payloads, telefone e tokens. Dependência fli fixada em revisão Git. Testes de domínio sem rede.

Limitações: servidor de desenvolvimento, destinatário único, banco sem criptografia própria e sem expiração automática, túnel temporário. Antes de uso público: consentimento, retenção/exclusão, limites, observabilidade, hospedagem estável e revisão das condições das fontes.
