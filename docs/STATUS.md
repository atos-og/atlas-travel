# Estado em 23/09/2026

O usuário confirmou respostas reais no WhatsApp de teste. A aplicação e a conta WhatsApp foram inscritas; acesso continua restrito ao destinatário local permitido.

Fluxo experimental implementado: confirmação, aeroportos, datas, adultos, preferências, normalização de ida/volta, até quatro resultados e seleção de links. Consulta em subprocesso limitado a 55 segundos, sem manter transação SQLite aberta durante a busca.

As consultas iniciais retornaram vazias. Uma nova execução real de CNF–GRU, ida 23/10/2026 e volta 30/10/2026, retornou ofertas para um e dois adultos pelo mesmo subprocesso usado pelo bot. Ranking e formatação exibiram quatro opções com links em ambos os casos. Detalhes e limites em [LIVE_VALIDATION.md](LIVE_VALIDATION.md). Não houve compra nem confirmação de preço no checkout.

Testes automatizados cobrem conversa, assinatura, duplicatas, acesso, datas, total de ida/volta, ranking, links, timeout e persistência. Não substituem validação externa.

Pendências: validação de preços e disponibilidade no site do fornecedor; estabilidade da fonte; crianças; datas flexíveis; ônibus; roteiros; preferências; monitoramento. Sem pagamento, emissão, reserva ou implantação pública do bot.

## Atualização de conversa e interface

O teste real do usuário terminou em sessão `complete`, com `success` e 38 ofertas recebidas. As respostas recentes foram entregues. Foram implementadas datas naturais em português, sinônimos de preferências/passageiros, listas, botões de confirmação e CTA URL nativo. A Meta aceitou a lista e o CTA no teste privado. Detalhes em [CONVERSATION.md](CONVERSATION.md).

## Busca por orçamento

Implementado teto total em BRL para todos os adultos, confirmação explícita, botão Sem limite, ajuste via comando/lista e filtro consistente entre ranking, lista e links. Acima do teto não é apresentado como oferta compatível. Refinamento da consulta anterior não dispara busca externa. 35 testes locais passaram, incluindo limites de centavos, remoção do teto, mensagens ambíguas, confirmação e menu de até dez linhas.
