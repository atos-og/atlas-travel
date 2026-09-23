# WhatsApp privado de teste

1. Crie um app Meta com o caso de uso WhatsApp e os recursos de teste disponibilizados pela conta.
2. Cadastre/verifique o destinatário de teste e confirme o envio de exemplo.
3. Copie `.env.example` para `.env`. Preencha access token, ID do número remetente, versão da Graph API e App Secret. Gere um verify token aleatório diferente do access token.
4. Configure `ATLAS_ALLOWED_WHATSAPP_USER` com DDI e número, somente dígitos, correspondente ao remetente dos eventos oficiais.
5. Execute `python -m atlas.webhook` no ambiente virtual. Use túnel HTTPS para a porta 8787 e callback `/webhook`, com o mesmo verify token.
6. Inscreva o campo `messages` da aplicação e a aplicação na conta WhatsApp (WABA). Verificar a URL sozinha não comprova entrega de eventos.
7. Ative `ATLAS_WHATSAPP_REPLIES_ENABLED=true`. Para voos, instale `requirements.txt` e ative `ATLAS_LIVE_FLIGHTS_ENABLED=true`.
8. Envie `cancelar` do usuário autorizado para começar uma sessão nova.

Telas e requisitos variam conforme a conta. Este guia descreve o projeto, não garante gratuidade ou requisitos de produção. Esta etapa usa o número de teste, sem registrar um número de produção.

## Diagnóstico

- `/health` identifica o servidor, não valida fontes externas.
- Callback verificada: desafio GET e verify token aceitos.
- POST assinado recebido: assinatura do App Secret validada.
- `sent`: API aceitou envio; entrega é confirmada separadamente pelos eventos `statuses`.
- `failed`: examine o código de erro local. Restrições de país/conta não se resolvem repetindo envios.
- Sem resposta: confira processo, túnel, token, assinaturas, destinatário permitido e fila.

Túnel temporário pode mudar de URL ao reiniciar; atualize a callback. Mantenha uma única instância de `atlas.webhook` com a Python do ambiente virtual. O servidor impede reutilização da porta.

## Dados locais

`work/conversations.db`: mensagens, respostas, remetente, ofertas e estado. `work/webhooks.db`: hashes dos eventos. Os bancos e `.env` ficam fora do Git. Envios incertos não são reenviados automaticamente. Use `cancelar` para recuperar uma conversa.
