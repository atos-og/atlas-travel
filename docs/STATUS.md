# Estado em 23/09/2026

O usuário confirmou respostas reais no WhatsApp de teste. A aplicação e a conta WhatsApp foram inscritas; acesso continua restrito ao destinatário local permitido.

Fluxo experimental implementado: confirmação, aeroportos, datas, adultos, preferências, normalização de ida/volta, até quatro resultados e seleção de links. Consulta em subprocesso limitado a 55 segundos, sem manter transação SQLite aberta durante a busca.

Consultas externas CNF–GRU e GRU–BOG com datas futuras retornaram `empty`. Nenhuma tarifa real foi validada nesta etapa. Isso não comprova ausência de voos e não é substituído por resultados fictícios.

Testes automatizados cobrem conversa, assinatura, duplicatas, acesso, datas, total de ida/volta, ranking, links, timeout e persistência. Não substituem validação externa.

Pendências: tarifas reais e links; estabilidade da fonte; crianças; orçamento; ônibus; roteiros; preferências; monitoramento. Sem pagamento, emissão, reserva ou implantação pública do bot.
