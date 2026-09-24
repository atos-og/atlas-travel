# Conversa natural e controles nativos

## Entrada em português

A conversa continua guiada por estado, mas aceita alternativas ao script numérico:

- `dia 23 de outubro desse ano`, `23 de outubro de 2027`, `23/10/2027` e `23/10`.
- `amanhã`, `depois de amanhã`, `daqui a 3 dias` e `em uma semana`.
- Na volta, `7 dias depois` e `uma semana depois` referem-se à data de ida.
- `somos duas pessoas`, `só eu`, `prefiro a mais barata`, `sem escalas` e `pode buscar`.
- `saio de Confins` e `quero ir para Bogotá` nos passos de origem/destino.

Usa-se horário de Brasília (UTC−3) para hoje/amanhã. Sem ano, assume o ano corrente e exibe a data interpretada; datas passadas são rejeitadas, nunca deslocadas silenciosamente ao próximo ano. Datas impossíveis, várias alternativas e expressões incompletas como `dia 23` exigem esclarecimento. A confirmação final sempre mostra DD/MM/AAAA antes de consultar.

Não é interpretação irrestrita por IA. Dias da semana isolados, pedidos contendo vários campos e correções arbitrárias ainda não são interpretados. O parser é local, sem serviço de IA ou custo de API.

## WhatsApp

- Passageiros: lista com seis opções de adultos.
- Preferências: lista com quatro critérios, sem confundir preço com conforto.
- Confirmação: botões `Confirmar busca` e `Recomeçar`.
- Resultados: lista com até quatro ofertas e ações para ajustar a viagem.
- Oferta selecionada: resumo e botão nativo de URL `Abrir oferta`, direcionado ao link retornado pelo Google Flights. Ainda não é checkout próprio nem link direto garantido da companhia.
- `ofertas` reapresenta as opções; os comandos digitados continuam funcionando.

Listas usam no máximo nove itens, títulos de até 24 caracteres e descrições de até 72; confirmações usam dois botões com títulos curtos. O corpo interativo fica limitado conservadoramente a 1.024 caracteres. Links extensos não são transformados em CTA; permanecem como texto.

Respostas `list_reply` e `button_reply` são tratadas pelos IDs, nunca pelo título enviado no evento. IDs aleatórios são vinculados à última mensagem de escolhas da sessão. Uma escolha antiga ou desconhecida não altera a viagem; o bot oferece as opções atuais. A deduplicação por ID da mensagem também cobre cliques. Ao selecionar uma oferta, o menu anterior fica obsoleto; use `ofertas` para reabrir.

O envio usa a mesma Graph API oficial e a mesma conversa ativa. Nenhum template pago ou serviço adicional foi contratado. Isso não garante gratuidade de uso em produção.

## Validação

28 testes locais: datas, ambiguidades, confirmação, payloads nativos, IDs antigos/falsos, fila, persistência, assinatura e voos. A Meta aceitou em teste real `interactive.type=cta_url` e `interactive.type=list` para o destinatário privado.

Referências: [exemplos oficiais de listas/botões da Meta](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/messages/interactive/) (SDK arquivado; payloads de lista/botão), [documentação de CTA URL](https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/interactive-cta-url-messages). A página de CTA retornou HTTP 429 durante a consulta; o formato foi validado também por envio real à API.
