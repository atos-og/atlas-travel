# Atlas

Assistente de viagens em desenvolvimento. Canal inicial: WhatsApp Cloud API oficial, em ambiente de testes. Telegram será alternativa se o WhatsApp exigir custos.

## Estado atual

Conversa guiada local e integração privada com WhatsApp: webhook assinado, fila SQLite, sessões persistentes e respostas de texto pela API oficial. Apenas o destinatário configurado pode conversar. Não consulta tarifas reais; fontes de voos, roteiros e alertas ainda serão implementados. Veja [configuração do webhook](docs/WHATSAPP_SETUP.md).

## Executar

Python 3.12 ou superior:

```sh
python -m atlas
python -m unittest discover -s tests -v
```

Digite `cancelar` para recomeçar e `sair` para encerrar. Datas usam DD/MM/AAAA. Cada sessão pertence a um identificador de usuário; este primeiro simulador guarda sessões apenas em memória.

## Decisões

- R$ 0 em serviços; uso privado durante a validação.
- Código de conversa independente do canal de mensagens.
- Nenhum preço, link ou busca será inventado.
- Preparar demonstração e código público separadamente de credenciais e dados reais.
- Não reutilizar tokens ou configurações privadas do Fly Club.
- Próximo marco: adaptar recepção e resposta do WhatsApp, validar assinatura do webhook, restringir destinatário e deduplicar eventos antes de conectar a fonte aérea.

## Configuração futura do WhatsApp

Começar pelo Developer Hub oficial: https://whatsappbusiness.com/developers/developer-hub/

Entrar com a conta Facebook, concluir o cadastro de desenvolvedor e procurar a configuração de WhatsApp para criar um aplicativo de teste. O caminho exato pode variar conforme a conta. Usar o número de teste disponibilizado pela Meta e cadastrar o destinatário de teste quando solicitado. Parar se houver solicitação de contratação ou cobrança.

A recepção de mensagens exige um webhook HTTPS acessível pela Meta. Para testes, usar túnel temporário gratuito conforme o guia. Executar apenas um programa local não torna esse endpoint acessível. O endereço temporário não faz parte do repositório.

`.env.example` lista os campos previstos. Não enviar tokens pelo chat nem versionar `.env`. As respostas exigem access token, phone number ID, versão da API, destinatário permitido e ATLAS_WHATSAPP_REPLIES_ENABLED=true. Por padrão ficam desativadas.

Mensagens e estado da conversa autorizada são armazenados somente no SQLite local ignorado pelo Git. Logs não exibem telefone ou texto. Duplicatas são filtradas pelo ID da mensagem. Falhas e envios incertos não são reenviados automaticamente; a sessão pode já ter avançado, então `cancelar` permite recomeçar. Confirmação da API é aceite para envio, não confirmação de entrega.

## Próximas entregas

1. Configuração de teste Meta e primeira mensagem de ida e volta.
2. Persistência local, validação de aeroportos e critérios completos de passageiros.
3. Adaptador aéreo revisado a partir do Fly Club, com ranking e links verificáveis.
4. Refinamento, datas flexíveis, roteiro e preferências.

Plano detalhado: [docs/PLAN.md](docs/PLAN.md).
