# Atlas

Assistente de viagens por conversa, desenvolvido como projeto de portfólio. Protótipo privado em Python com WhatsApp Cloud API oficial, sessões persistentes e consulta experimental de voos.

## Recursos

- Aeroportos, datas de ida/volta, 1 a 6 adultos e confirmação antes da consulta.
- Menor preço, menor duração, sem paradas ou maior preço entre as ofertas retornadas.
- Até quatro ofertas com total de ida e volta, horários, companhias, duração e links no Google Flights quando a fonte retorna dados válidos.
- Comandos `ajuda`, `filtros`, `datas`, `passageiros`, `buscar`, `link 1` e `cancelar`.
- Webhook HMAC, destinatário permitido, fila SQLite, deduplicação e status de entrega.

**Fonte aérea em validação:** consultas reais em 23/09/2026 retornaram vazias. Ainda não foi validada uma tarifa real nesta integração. O bot informa o resultado sem inventar preços. Testes automatizados usam dados sintéticos e não comprovam disponibilidade externa.

Ônibus, roteiros, orçamento, alertas e preferências são próximos marcos. O fluxo atual é guiado e não usa IA.

## Executar

Python 3.12+ e Git. Simulador e testes não precisam de dependências externas:

```sh
python -m atlas
python -m unittest discover -s tests -v
```

Para o webhook e a fonte experimental, crie um ambiente virtual, instale `requirements.txt`, copie `.env.example` para `.env` e configure conforme [o guia](docs/WHATSAPP_SETUP.md). Execute `python -m atlas.webhook` usando esse ambiente. Servidor: `127.0.0.1:8787`. A callback precisa de HTTPS externo. Respostas e consultas externas ficam desativadas por padrão.

Exemplo: `oi` → `Confins` → `Bogotá` → data da ida → data da volta → `1` adulto → `1` menor preço → `sim`. Datas futuras em DD/MM/AAAA. `São Paulo` e `Colômbia` pedem escolha de aeroporto. O comando `python -m atlas` continua sendo uma demonstração sem internet.

## Limitações

Fonte não oficial de Google Flights, sujeita a mudanças. Não cobre todas as fontes nem garante o menor preço do mercado. Links levam ao Google Flights, não a checkout próprio. Bagagem, reembolso e conforto não são inferidos do preço. Apenas econômica, ida e volta e adultos nesta versão.

Operação inicial sem contratação de serviços, em teste privado. Isso não garante gratuidade do WhatsApp em produção. Computador, túnel e processo precisam estar ativos. Não está pronto para atendimento público.

## Documentação

- [Plano e diferenciais](docs/PLAN.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Estado da validação](docs/STATUS.md)
- [WhatsApp](docs/WHATSAPP_SETUP.md)
- [Segurança](SECURITY.md)

Adaptação seletiva do [Fly Club](https://github.com/atos-og/flyclub), também de Atos Barros. [Atribuições](THIRD_PARTY_NOTICES.md). Licença MIT.
