# Validação do webhook do Atlas

## Atualização: conversa privada

O receptor agora pode enfileirar textos e responder pela API oficial quando ATLAS_WHATSAPP_REPLIES_ENABLED=true. Exige ATLAS_ALLOWED_WHATSAPP_USER em formato internacional sem sinal +, WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID e META_GRAPH_API_VERSION. Sem destinatário autorizado, não enfileira conversas. O teste continua sem tarifas reais.

A fila conversations.db guarda texto, remetente e sessão localmente, fora do Git. Eventos de status não geram respostas. Janela conservadora de 23 horas para enviar; sem templates proativos. Cada ID recebido gera no máximo uma tentativa automática: timeout e reinício durante envio ficam como uncertain e exigem análise, pois a API pode já ter aceitado a mensagem. Erros não são impressos com conteúdo ou credenciais. Os parágrafos abaixo sobre receptor sem envio descrevem o marco anterior.

## Estado conhecido

- Usuário confirmou recebimento de Hello World no destinatário colombiano.
- Tentativa com destinatário brasileiro retornou 130497. Isso é uma restrição observada nessa conta, não prova de bloqueio geral ao Brasil.
- O painel exibiu que aplicativo não publicado recebe apenas testes do dashboard. Recepção de conversa real permanece não validada; não publicar o aplicativo nem adicionar pagamento automaticamente.
- O receptor implementado apenas confirma desafios e recebe eventos assinados. Não envia mensagens, não processa conversas e não chama provedores de tarifas.

## Configuração local

1. Copiar `.env.example` para `.env` sem sobrescrever configuração existente.
2. Criar um WHATSAPP_VERIFY_TOKEN aleatório. É o token de verificação que será colado no painel.
3. Obter o App Secret nas configurações básicas do aplicativo Meta e salvá-lo em META_APP_SECRET, somente no `.env` local. É diferente do access token e do verify token.
4. Executar `python -m atlas.webhook` a partir da raiz do projeto. Variáveis são relidas a cada requisição; mudanças no `.env` não exigem reinício.
5. Executar `cloudflared tunnel --url http://127.0.0.1:8787` para abrir um túnel de desenvolvimento gratuito. Instalar cloudflared pela distribuição oficial. O endereço pode mudar ao reiniciar.
6. Na Meta, configurar Callback URL como `https://ENDERECO-DO-TUNEL/webhook` e Verify token com o mesmo WHATSAPP_VERIFY_TOKEN local. Clicar Verify and save.
7. Na configuração de campos de webhook, habilitar `messages`, se oferecido, e usar o teste do painel. Conferir no log local `Signed webhook received.`

Somente os passos efetivamente executados devem ser declarados concluídos. Uma verificação GET aprovada não confirma recepção POST nem conversa real. Sem META_APP_SECRET, POST retorna 503; assinatura ausente ou inválida retorna 403.

## Limites

Receptor HTTP da biblioteca padrão, destinado somente a teste temporário; substituir por servidor de aplicação adequado antes de produção. Vinculado ao loopback, não serve arquivos, não imprime tokens ou corpo das mensagens. Grava somente hash do payload e horário em SQLite ignorado pelo Git. Deduplicação é do payload idêntico; processamento futuro precisa de deduplicação por ID de mensagem. Não é uma fila de mensagens e não retém conteúdo para processamento posterior.

Os processos local e de túnel precisam continuar ativos. Encerrá-los desativa o endpoint. Nenhum token ou endereço temporário deve entrar na documentação pública.

Fonte do túnel: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/
