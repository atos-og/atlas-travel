# Atlas — plano do assistente de viagens

Data: 23/09/2026. Status: planejamento aprovado para início do desenvolvimento; nenhum novo bot ou repositório foi publicado nesta etapa. Nome escolhido pelo usuário: Atlas.

## Decisões confirmadas para a primeira fase

Atualização de canal: o usuário escolheu WhatsApp Cloud API oficial em ambiente de testes, mantendo orçamento zero. Telegram passa a ser alternativa caso o WhatsApp exija custos. As referências ao Telegram abaixo descrevem a proposta anterior; os fluxos de produto serão adaptados ao WhatsApp. Não contratar serviços para viabilizar a mudança. Cadastro Meta ainda não configurado. Base inicial criada em outputs/atlas: simulador guiado local sem tarifas, sem IA e sem conexão ao WhatsApp, com quatro testes aprovados.

- Orçamento de serviços: R$ 0. Não contratar serviços, usar créditos que exijam cobrança automática ou depender de testes pagos para o funcionamento básico.
- Uso pessoal e privado durante a validação. Código público continua sendo objetivo de portfólio; acesso público ao bot é uma decisão independente e posterior.
- Executar inicialmente no computador do usuário, sem hospedagem contratada. Atendimento e monitoramento local funcionam apenas enquanto o processo estiver ativo e conectado.
- Primeira interação proposta: conversa guiada com botões, comandos e interpretação limitada e explícita. Conversação livre e geração de roteiros por IA continuam no objetivo, mas dependem de validar uma alternativa sem custo compatível com o computador ou com limites gratuitos sustentáveis.
- Implementar uma interface substituível para interpretação de linguagem; o fluxo básico e o ranking não devem exigir uma API de IA.
- Persistência local independente: avaliar SQLite para o protótipo pessoal, evitando configuração de servidor e mantendo possível migração para PostgreSQL. A regra PostgreSQL do Fly Club permanece restrita àquele projeto.
- Primeiro marco: busca aérea, filtros, resultados explicados e refinamento. Começar com provedor demonstrativo; validar o adaptador real do Fly Club antes de habilitá-lo. Sem copiar credenciais nem configurações pessoais do projeto original.
- Restringir o bot ao identificador Telegram autorizado antes de conectar a busca real. Não adicionar custos ou abrir acesso ao público sem nova decisão do usuário.

Estas decisões prevalecem sobre a arquitetura alvo e o cronograma de publicação descritos abaixo. A adoção de IA, PostgreSQL hospedado e operação contínua será reavaliada depois da validação local.

## 1. Objetivo e posicionamento

Permitir que uma pessoa encontre, compare e acompanhe transportes e planeje sua viagem em uma conversa. Interface inicial: Telegram, em português brasileiro. Compra concluída no fornecedor, fora do bot.

Proposta: “Encontre a viagem que combina com seu orçamento, seu tempo e seu jeito de viajar.”

O projeto será independente do Fly Club, com código público e operação privada. A diferenciação pretendida combina escolha explicável, comparação de transportes, orçamento, roteiro e memória. Não há evidência suficiente para afirmar que cada recurso é exclusivo em relação à Passabot.

## 2. Avaliação para portfólio

É um projeto forte se demonstrar um fluxo real de ponta a ponta: mensagem → critérios estruturados → consulta externa → comparação verificável → refinamento → roteiro ou alerta. Mostra modelagem de domínio, integração de APIs, persistência, processamento assíncrono, uso delimitado de IA, testes e operação.

Riscos para o portfólio: escopo grande sem conclusão, preços inventados, demonstração dependente de credenciais inacessíveis, cópia excessiva do Fly Club e complexidade sem necessidade.

Entregáveis de apresentação: README em inglês com guia em português, vídeo curto, desenho de arquitetura, decisões técnicas, modo demonstrativo com dados explicitamente fictícios, instruções reproduzíveis, testes das regras críticas e métricas medidas. Não inventar usuários, economia ou desempenho.

## 3. O que foi verificado no Fly Club

Fontes locais consultadas: AGENTS.md, README.md, docs/ARCHITECTURE.md, docs/STATUS.md, docs/PUBLICATION.md, pyproject.toml, models.py e o adaptador google_flights.py; também a tarefa “Desenvolvimento” no Codex. Remoto identificado: https://github.com/atos-og/flyclub.

Base existente: Python 3.12+, fronteira FlightProvider, fli como integração não oficial com Google Flights, modelos normalizados, Decimal, PostgreSQL, buscas flexíveis, histórico, avaliação determinística, deduplicação e envio ao Telegram.

Limitações verificadas relevantes:

- O modelo de rota atual exige ida e volta; ida simples precisa de adaptação.
- FlightOption contém preço, trechos, paradas e duração, mas não bagagem nem regras completas de tarifa.
- O adaptador inspecionado preenche google_flights_url e deixa booking_url vazio. O botão inicial deve dizer “Ver oferta no Google Flights”, sem prometer checkout direto.
- O envio atual ao Telegram não equivale a um atendimento com sessões e usuários independentes.
- O monitor é baseado em execuções periódicas; um chat interativo precisa de um processo disponível para receber mensagens.
- O Deal Score avalia oportunidade histórica. Ele não deve ser reutilizado como nota de conforto ou adequação pessoal.

Reaproveitar componentes pequenos após revisão e com referência ao commit de origem. Manter atribuições e licenças aplicáveis. Evitar copiar histórico Git, configurações privadas ou banco de produção. Não extrair uma biblioteca compartilhada nem alterar o Fly Club antes de haver necessidade concreta; iniciar com reaproveitamento seletivo documentado.

## 4. Jornada principal

1. Usuário inicia a conversa ou descreve uma viagem completa.
2. Bot identifica intenção e reaproveita os dados já fornecidos.
3. Pergunta apenas o necessário: origem, destino, datas/janela, ida/volta, passageiros e condições relevantes.
4. Resolve ambiguidades: país sem cidade, “sexta” sem contexto, BH como cidade versus CNF como aeroporto, orçamento por pessoa versus grupo.
5. Mostra um resumo dos critérios e consulta as fontes habilitadas.
6. Retorna até quatro opções distintas com preço, motivo da seleção, fonte e horário da consulta.
7. Usuário abre uma oferta, refina, compara datas, salva ou cria alerta.
8. Bot sugere roteiro contextualizado à viagem escolhida.

O estado da conversa precisa suportar voltar, cancelar, corrigir informação e iniciar outra viagem. Cada busca tem versão: resposta atrasada de uma busca anterior não substitui a atual. Abrir um link não confirma uma compra.

## 5. Escolhas, filtros e ordenação

Separar restrições obrigatórias de preferências. “Sem paradas” exclui opções com paradas; “prefiro mais rápido” ordena as opções restantes. Nunca relaxar uma restrição silenciosamente.

| Grupo | Opções planejadas | Regra |
|---|---|---|
| Preço | Menor ou maior preço, teto de gasto | Comparar moeda, passageiros e escopo equivalentes |
| Tempo | Menor duração, horário de saída/chegada | Ida e volta visíveis separadamente |
| Paradas | Sem paradas, máximo de paradas, limite de conexão | Usar informação confirmada; não inferir ausência de parada pelo marketing “direto” |
| Conforto aéreo | Cabine, menos conexões, evitar madrugada | Nota explicada apenas com atributos disponíveis |
| Conforto rodoviário | Convencional, executivo, semileito, leito | Dependente dos dados do fornecedor |
| Bagagem | Item pessoal, cabine, despachada | Campo desconhecido não equivale a bagagem incluída |
| Flexibilidade | Datas próximas, cancelamento/remarcação | Regras tarifárias só quando fornecidas e verificáveis |
| Localização | Aeroportos e terminais alternativos | Alteração explícita, com deslocamento estimado |

Ordenar por maior preço será possível, mas “mais caro” nunca será tratado como sinônimo de melhor qualidade.

Ranking inicial: mais barata, mais rápida e melhor equilíbrio. Uma quarta opção de conforto só aparece quando os dados sustentarem a comparação. Não repetir a mesma oferta para preencher quatro cartões. Explicar o equilíbrio por diferenças concretas de preço, duração e conexões; pesos e desempates devem ser determinísticos e testáveis.

## 6. Diferenciais e entregas

| Recurso | Primeira entrega | Evolução |
|---|---|---|
| Roteiro personalizado | Dias, interesses, ritmo e orçamento; edição pelo chat | Proximidade, mapas e atualização de informações externas |
| Memória de preferências | Salvar origem, cabine e interesses com autorização | Aprender com escolhas confirmadas, com edição e exclusão |
| Planejamento integrado | Reaproveitar datas e horários da opção salva | Consolidar orçamento e múltiplas etapas |
| Busca por orçamento | Confirmar se orçamento é só transporte ou viagem inteira | Explorar destinos em um catálogo e janela limitados |
| Avião × ônibus | Prova de integração rodoviária e equivalência de preços | Comparação de custo e duração porta a porta |

Busca por orçamento total deve separar transporte cotado de hospedagem, alimentação e passeios estimados. Não apresentar um pacote confirmado sem cotações correspondentes. Explorar destinos precisa limitar destinos, datas e chamadas; nunca tentar consultar o mundo inteiro a cada mensagem.

Roteiros devem respeitar chegada, partida, deslocamentos e tempo de descanso. Horários, ingresso e disponibilidade exigem fonte e data de consulta; dados ausentes aparecem como pendentes. Roteiro é planejamento, não reserva. O usuário pode pedir “mais barato”, “menos corrido” ou “trocar esse passeio” preservando o restante.

## 7. Descoberta de funcionalidades

Usar menu permanente e até três sugestões contextuais por resposta. Só sugerir funções habilitadas.

- Início: Buscar passagem / Explorar destinos / Montar roteiro.
- Resultados: Alterar filtros / Comparar datas / Monitorar preço.
- Oferta salva: Montar roteiro / Planejar gastos / Salvar preferência.
- Roteiro: Reduzir gastos / Diminuir ritmo / Trocar passeio.
- Menu: Minhas viagens / Meus alertas / Preferências / Ajuda.

Comandos propostos: /start, /help, /buscar, /roteiro, /viagens, /alertas, /preferencias e /cancelar. Preferir também linguagem natural. Não interromper uma tarefa com publicidade de funcionalidades.

## 8. Arquitetura proposta

Começar com uma aplicação Python modular, com processo do bot e worker de tarefas demoradas. Banco PostgreSQL para sessões, viagens, preferências, buscas, ofertas e alertas. No desenvolvimento, receber mensagens por long polling; avaliar webhook na implantação conforme hospedagem escolhida. Não usar GitHub Actions como servidor da conversa.

Módulos: telegram, conversation, domain, search, ranking, providers, itinerary, monitoring e storage. Interfaces separadas para voos, ônibus, lugares e interpretação de linguagem. Evitar microserviços e adicionar Redis ou outra fila apenas se o volume demonstrar necessidade; uma fila persistente no banco atende à primeira arquitetura proposta.

A IA interpreta texto, propõe dados estruturados e redige roteiros/explicações. Código valida critérios, chama ferramentas, calcula valores, ordena opções e controla permissões. Preços e links exibidos vêm das ferramentas. Respostas não podem alegar uma busca que não aconteceu.

Entidades mínimas: User, Preference, ConversationSession, Trip, SearchRequest, OfferSnapshot, Watch, AlertDelivery, Itinerary e ItineraryDay. Dados sempre associados ao usuário autorizado. Processamento idempotente de updates, retomada após reinício e controle de buscas simultâneas por conversa.

## 9. Fontes e custos

Começar avaliando o adaptador fli existente para o protótipo. Integração não oficial pode mudar ou falhar; adequação a um bot público, cobertura, capacidade, termos e estabilidade precisam ser avaliados antes de uma abertura ampla. Não prometer abrangência total nem menor preço de mercado.

Ônibus depende de uma fonte real e acesso autorizado. A ClickBus tem documentação para parceiros, mas documentação pública não confirma credenciais, aprovação comercial, custos ou suporte ao encaminhamento de compra desejado. Enquanto não houver acesso, manter demonstrador rodoviário rotulado e função real desabilitada.

Planejar limites por usuário, prazo máximo de busca, cache com idade visível, orçamento de chamadas, poucas tentativas e notificações apenas relevantes. Definir teto mensal antes de contratar hospedagem, IA ou APIs. Telegram não elimina esses custos. A implantação 24/7 depende da hospedagem escolhida; execução local serve para desenvolvimento.

## 10. Sequência de desenvolvimento e critérios de conclusão

### Etapa 0 — Prova técnica e base pública

Criar repositório limpo com nome definitivo, licença, README, ambiente de exemplo, CI e demonstração sintética. Medir o adaptador aéreo em amostra controlada: cobertura, latência, campos e qualidade dos links. Registrar matriz de capacidades e investigar acesso rodoviário em paralelo ao planejamento, sem depender dele para o primeiro fluxo.

Concluída quando: busca normalizada e link utilizável validados, limitações documentadas e instalação demonstrativa reproduzível sem credenciais reais.

### Etapa 1 — Consulta aérea conversacional

Receber mensagens, completar critérios, buscar voos, aplicar restrições, ordenar, mostrar até quatro opções e refinar. Implementar sessão persistente, erros úteis, cancelamento e modo demo. Priorizar ida e volta compatível com a base; validar ida simples antes de anunciá-la.

Concluída quando: uma pessoa realiza consulta e refinamento de ponta a ponta no Telegram; dois usuários não acessam dados um do outro; resultados vazios, timeout e fonte indisponível têm respostas distintas.

### Etapa 2 — Primeira versão diferenciada

Adicionar roteiro editável a partir da viagem salva, preferências opcionais, sugestões contextuais, datas flexíveis limitadas e alertas com editar/pausar/excluir. Separar histórico de oportunidade de ranking pessoal. Declarar falta de histórico em novos alertas.

Concluída quando: viagem escolhida gera roteiro coerente, edição preserva dados anteriores e alerta persiste após reinício sem duplicação por reprocessamento. Esta é a primeira versão recomendada para apresentação pública do produto.

### Etapa 3 — Orçamento e transportes

Adicionar exploração limitada por orçamento e integração rodoviária real após aprovação de acesso. Mostrar custos conhecidos e estimados separadamente, duração porta a porta quando sustentada e filtros de categoria.

Concluída quando: comparação usa o mesmo escopo de passageiros, datas e moeda, informa cobertura e não classifica estimativas como cotações.

### Etapa 4 — Publicação e operação

Publicar demonstração, vídeo, decisões de arquitetura e resultados medidos. Executar testes de isolamento, classificação, persistência, recuperação, deduplicação e integração por contratos. Verificar repositório e histórico sem credenciais ou viagens reais. Habilitar bot público com quotas, política de dados e observabilidade agregada.

Indicadores: tempo mediano e P95 até resultado, falhas por fonte, consultas concluídas, custo por consulta, cliques de oferta, roteiros solicitados e alertas duplicados. Clique não mede venda; usuário de demonstração não mede adoção real.

## 11. Fora do primeiro escopo

Checkout, emissão própria, pagamentos, programa de milhas, previsão garantida de queda de preços, aplicativo móvel, dashboard complexo, mensagens por áudio e ingestão de documentos pessoais. Podem ser avaliados após uso real; não são necessários para provar o produto.

## 12. Fontes externas

- Telegram: botões, comandos e menu — https://core.telegram.org/bots/features
- ClickBus: documentação de integração para parceiros — https://developer.clickbus.com.br/docs/getting-started
- Fly Club: repositório identificado pelo remoto local — https://github.com/atos-og/flyclub

Próxima entrega: base local do Atlas e uma primeira fatia da etapa 1 (mensagem → critérios → busca aérea → opções ordenadas → refinamento), respeitando orçamento zero e uso privado. A conexão ao Telegram depende da criação de um bot próprio e configuração segura do token. A escolha de uma solução gratuita de IA permanece aberta e não bloqueia o modo guiado.
