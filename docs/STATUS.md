# Estado do Atlas

## Implementado e validado localmente

- Simulador de conversa guiada independente de canal.
- Receptor de testes HTTP em loopback: desafio de verificação, assinatura HMAC SHA-256, limites de corpo e timeout.
- Recebimentos persistidos apenas como hash e horário; nenhuma mensagem enviada automaticamente.
- Sete testes unitários passaram. Health check e desafio GET também passaram via HTTP local.
- Configuração privada ignorada pelo Git; segredo da Meta ainda depende de preenchimento pelo usuário.
- Repositório Git local iniciado, com plano e instruções. Publicação no GitHub ainda não realizada.

## Pendente

- Salvar META_APP_SECRET localmente e validar POST assinado enviado pela Meta.
- Salvar Callback URL e Verify token no painel e habilitar campo messages se aplicável.
- Validar as condições de recebimento de mensagens reais segundo o aviso de publicação do painel.
- Implementar processamento por ID de mensagem, destinatário permitido e resposta pela API.
- Integrar fontes reais de tarifas e demais funcionalidades do plano.

Não confundir recebimento técnico do webhook com bot conversacional completo. A etapa atual não exige access token nem contrata serviços.
