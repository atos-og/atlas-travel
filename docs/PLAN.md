# Plano do Atlas

Objetivo: consultar e refinar viagens pelo WhatsApp, comparar alternativas e abrir links de fornecedores. Repositório público de portfólio, operação privada inicialmente sem contratação de serviços. Telegram permanece alternativa de canal.

## Marcos

1. **Conversa privada — implementada:** webhook, respostas, sessões, deduplicação e destinatário restrito.
2. **Busca aérea — em validação:** fluxo, ranking, links e erros implementados. Falta obter tarifas reais e conferir total dos passageiros, ida/volta, aeroportos, datas e link. As consultas iniciais retornaram vazias.
3. **Orçamento e refinamento:** teto de preço, datas flexíveis com limite de consultas e destinos sugeridos. Separar estimativas de tarifas verificadas.
4. **Avião e ônibus:** selecionar fonte rodoviária viável. Comparar total, duração, paradas, terminais e categoria informada; deslocamento terrestre quando houver dados.
5. **Roteiro personalizado:** interesses, dias, ritmo e orçamento; passeios por proximidade. Horários/preços com fonte, data e confirmação quando necessária.
6. **Preferências e alertas:** salvar escolhas com opção de apagar. Monitoramento exige fonte estável e avaliação do custo de mensagens proativas.

## Diferenciais

Comparação avião × ônibus; busca por orçamento; roteiro personalizado; memória de preferências; sugestões contextuais dos recursos disponíveis. Após escolher voo, oferecer roteiro; diante de preço alto, sugerir outras datas ou transportes. Recursos futuros não serão apresentados como disponíveis. `ajuda` já distingue os dois.

## Portfólio

O valor técnico está na integração real, estado de conversa, normalização de tarifas, segurança e tratamento de falhas. Prioridade: validar a fonte aérea antes de adicionar IA ou ônibus. Uma futura IA deverá transformar pedidos em critérios validados; preços e links continuarão vindo das fontes.
