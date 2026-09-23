# Estado do Atlas

## Implementado e validado localmente

- Simulador de conversa guiada independente de canal.
- Receptor de testes HTTP em loopback: desafio de verificação, assinatura HMAC SHA-256, limites de corpo e timeout.
- Recebimentos persistidos apenas como hash e horário; nenhuma mensagem enviada automaticamente.
- Sete testes unitários passaram. Health check e desafio GET também passaram via HTTP local.
- Configuração privada ignorada pelo Git; App Secret e access token preenchidos pelo usuário. Token validado pela API como pertencente ao Atlas, com permissões de gerenciamento e mensagens WhatsApp.
- Webhook reconfigurado pela API após restauração dos processos locais. GET de subscriptions confirmou callback ativo e campo messages (versão retornada v26.0).
- POST subscribed_apps aprovado; consulta posterior confirmou Atlas vinculado à conta de teste. Aplicativo interno da Meta mantido.
- Repositório Git local iniciado, com plano e instruções. Publicação no GitHub ainda não realizada.

## Pendente

Atualização: respostas privadas implementadas com fila por ID da mensagem, sessão persistida e allowlist obrigatória. Onze testes passaram, incluindo duplicação, remetente não autorizado, mensagens antigas e resultado incerto. Ativação e entrega real devem ser verificadas separadamente.

- Validar POST de mensagem real enviado pela Meta. Não confundir teste sintético local com entrega real da plataforma.
- Validar as condições de recebimento de mensagens reais segundo o aviso de publicação do painel.
- Validar conversa completa com o usuário pelo WhatsApp; integração implementada e testada com transportes simulados.
- Integrar fontes reais de tarifas e demais funcionalidades do plano.

Não confundir recebimento técnico do webhook com bot conversacional completo. A etapa atual não exige access token nem contrata serviços.
