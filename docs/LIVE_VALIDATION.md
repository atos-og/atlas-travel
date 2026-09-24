# Validação externa — 23/09/2026 (Brasília)

Executado `atlas.flights.search`, que usa o mesmo subprocesso limitado a 55 segundos do bot. Fonte: Google Flights através do fli fixado em requirements.txt. Rota sintética de teste: CNF → GRU, ida 23/10/2026, volta 30/10/2026, econômica, menor preço.

| Adultos | Horário UTC | Ofertas normalizadas | Exibidas | Menor total retornado | Links nas exibidas |
| --- | --- | --- | --- | --- | --- |
| 1 | 24/09/2026 01:05 | 37 | 4 | R$ 683,00 | 4 |
| 2 | 24/09/2026 01:06 | 36 | 4 | R$ 1.430,00 | 4 |

Mensagens formatadas com 971 e 979 caracteres, abaixo do limite de texto utilizado. Datas, aeroportos, BRL, jornadas completas e preços positivos passam pela normalização do adaptador. Links retornados são HTTPS no domínio Google.

Os valores são observações históricas da consulta, não ofertas garantidas. O total para dois adultos vem de uma nova consulta, não da multiplicação do resultado para um adulto. A disponibilidade por faixa tarifária pode mudar.

Não foram validados: abertura e preço final no checkout, bagagem/reembolso, emissão, nem entrega desses resultados pelo fluxo completo de uma conversa real no WhatsApp. As consultas anteriores haviam retornado vazias; não houve alteração do adaptador para obter sucesso, portanto a causa daquela indisponibilidade não foi determinada.
