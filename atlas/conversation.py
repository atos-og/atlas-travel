"""Channel-independent guided travel conversation with optional live search."""

from dataclasses import dataclass, field
from datetime import date, datetime
from .language import local_today, parse_date, choice, clean, is_greeting, is_confirmation
from .budget import parse_budget, BUDGET_PROMPT, label, money


PRIORITY_PROMPT = (
    '*Como você quer comparar as ofertas?*\n\n'
    '1. *Menor preço*\n'
    '2. *Menor duração*\n'
    '3. *Sem paradas*\n'
    '4. *Maior preço* entre as ofertas encontradas\n\n'
    'Abra a lista abaixo ou responda com o número da opção.'
)

OFFLINE_PRIORITY_PROMPT = (
    '*Como você quer comparar as opções?*\n\n'
    '1. *Menor preço*\n'
    '2. *Menor duração*\n'
    '3. *Sem paradas*\n\n'
    'Responda com o número da opção.'
)

FLEXIBILITY_PROMPT = (
    '*Quer comparar datas próximas?*\n\n'
    'Posso consultar até 3 combinações:\n'
    '• As datas que você informou\n'
    '• Um dia antes\n'
    '• Um dia depois\n\n'
    'A ida e a volta mudam juntas, mantendo a duração da viagem.\n'
    'Não é uma busca do mês inteiro.\n\n'
    '*O que você prefere?*\n'
    'Escolha comparar ±1 dia ou manter as datas exatas.'
)

FAQ_RESPONSES = {
    'duvida bagagem': ('*Bagagem e regras da tarifa*\n\nAtlas ainda não confirma bagagem incluída, marcação de assento, alteração ou reembolso. '
                       'Confira essas condições no fornecedor antes de comprar.'),
    'duvida compra': ('*Compra da passagem*\n\nAtlas não vende, reserva nem recebe pagamentos. O botão abre a fonte da oferta; '
                      'confirme passageiros, datas, bagagem, regras e total antes de concluir por lá.'),
    'duvida precos': ('*Sobre os preços*\n\nAs tarifas são uma fotografia da consulta e podem mudar no fornecedor. '
                      'Atlas compara apenas as opções retornadas pela fonte e não garante o menor preço de todo o mercado.'),
    'duvida privacidade': ('*Seus dados no Atlas*\n\nA conversa e as preferências ficam no armazenamento privado do serviço. '
                          'Quando a interpretação inteligente é necessária, apenas a mensagem atual e um contexto curto da etapa são enviados ao Groq; '
                          'preços, telefone e credenciais não entram nesse pedido.'),
    'duvida onibus': ('*Passagens de ônibus*\n\nO fluxo rodoviário já está implementado, mas Atlas ainda não consulta tarifas ao vivo nesta instalação. A fonte oficial escolhida exige credenciamento de parceiro antes da ativação. Digite *ônibus* para ver o estado da integração.'),
    'duvida alertas': ('*Alertas de preço*\n\nAtlas ainda não monitora preços em segundo plano nem envia alertas automáticos. Hoje, cada busca acontece quando você pede.'),
    'duvida cobertura': ('*O que Atlas cobre hoje*\n\nAtlas consulta voos de ida e volta para adultos, compara orçamento e datas próximas, guarda preferências quando você pede e monta roteiros para São Paulo, Bogotá ou Rio de Janeiro.\n\nDigite *menu* para ver as opções.'),
    'duvida conforto': ('*Conforto e qualidade*\n\nAtlas pode comparar preço, duração e quantidade de paradas. Ainda não avalia espaço do assento, serviço de bordo, bagagem ou qualidade da cabine.'),
    'obrigado atlas': ('Por nada! 😊\n\nQuando quiser continuar, digite *menu* para consultar voos, explorar destinos ou montar um roteiro.'),
}

BRAZIL_AIRPORTS = {'CNF', 'GRU', 'CGH', 'VCP', 'GIG', 'SDU', 'BSB', 'SSA',
                   'REC', 'FOR', 'FLN', 'POA', 'CWB'}


def trip_summary(session):
    values = session.values
    itinerary = values.get('_itinerary', {})
    bus = values.get('_bus', {})
    has_flight = any(values.get(key) for key in ('origin', 'destination', 'departure', 'return'))
    has_itinerary = itinerary.get('plan') is not None
    has_bus = bool(bus.get('result'))
    if not has_flight and not has_itinerary and not has_bus:
        return ('*Resumo da viagem*\n\nVocê ainda não confirmou dados de voo nem montou um roteiro. '
                'Digite *menu* para começar.')
    lines = ['*Resumo da sua viagem*']
    if has_flight:
        lines += ['', '*Passagens*']
        if values.get('origin') or values.get('destination'):
            lines.append(f"• Rota: {values.get('origin', '?')} → {values.get('destination', '?')}")
        if values.get('departure'):
            lines.append(f"• Ida: {values['departure']}")
        if values.get('return'):
            lines.append(f"• Volta: {values['return']}")
        if values.get('adults'):
            lines.append(f"• Passageiros: {values['adults']} adulto(s)")
        if values.get('budget') is not None:
            lines.append(f"• Orçamento total: R$ {money(values['budget'])}")
        result = values.get('result', {})
        if result.get('status') == 'success':
            lines.append(f"• Consulta salva: {len(result.get('offers', []))} opção(ões) retornada(s)")
            if result.get('checked_at'):
                lines.append(f"• Horário da consulta: {result['checked_at']}")
    if has_itinerary:
        from .destinations import CITIES
        lines += ['', '*Passeios*', f"• Cidade: {CITIES[itinerary['city']]}",
                  f"• Duração: {itinerary['days']} dia(s)",
                  f"• Interesses: {itinerary['interest']}",
                  f"• Ritmo: {itinerary['pace']}"]
    if has_bus:
        lines += ['', '*Ônibus*', f"• Rota: {bus.get('origin', '?')} → {bus.get('destination', '?')}",
                  f"• Ida: {bus.get('departure', '?')}",
                  f"• Passageiros: {bus.get('adults', '?')} adulto(s)"]
        if bus.get('result', {}).get('status') == 'success':
            lines.append(f"• Consulta salva: {len(bus['result'].get('offers', []))} opção(ões) retornada(s)")
    lines += ['', 'Preços, horários, documentos e disponibilidade devem ser conferidos antes da viagem.',
              '', 'Digite *checklist da viagem* para revisar os preparativos.']
    return '\n'.join(lines)


def travel_checklist(session):
    values = session.values
    destination = values.get('destination')
    international = bool(destination and destination not in BRAZIL_AIRPORTS)
    route = f" para {destination}" if destination else ''
    lines = [f"*Checklist da viagem{route}*", '', '*Documentos*']
    if international:
        lines += ['□ Passaporte válido para todo o período.',
                  '□ Conferir visto, entrada, vacinas e permanência em fontes oficiais do destino.']
    else:
        lines.append('□ Documento oficial aceito pela transportadora e dentro da validade.')
    lines += ['', '*Passagens e hospedagem*',
              '□ Conferir nomes, aeroportos, datas e quantidade de passageiros.',
              '□ Revisar bagagem, check-in, alteração e reembolso diretamente no fornecedor.',
              '□ Salvar reservas e endereços para acesso offline.',
              '', '*Durante a viagem*',
              '□ Planejar deslocamento entre aeroporto, hospedagem e passeios.',
              '□ Conferir clima, horários e disponibilidade perto da data.',
              '□ Separar medicamentos, contatos de emergência e meios de pagamento.',
              '', 'Esta lista é um apoio geral. Regras oficiais e necessidades pessoais podem exigir outros itens.']
    return '\n'.join(lines)


@dataclass
class Session:
    step: str = "origin"
    values: dict = field(default_factory=dict)


class Conversation:
    def __init__(self, flight_search=None, on_search=None, preferences=None, interpreter=None, bus_search=None):
        self.sessions: dict[str, Session] = {}
        self.flight_search = flight_search
        self.on_search = on_search
        from .preferences import Preferences
        self.preferences = preferences if preferences is not None else Preferences()
        self.interpreter = interpreter
        self.bus_search = bus_search

    def reply(self, user_id: str, text: str, *, today: date | None = None) -> str:
        text = text.strip()
        today = today or local_today()
        # A standalone greeting starts a new planning session. Longer messages
        # such as "bom dia, quero ir de..." are not classified as greetings and
        # still keep every explicitly supplied trip field.
        if is_greeting(text):
            self.sessions.pop(user_id, None)
        current = self.sessions.get(user_id)
        if self.interpreter:
            try:
                step = current.step if current else 'origin'
                context = current.values if current else {}
                if current and current.values.get('_itinerary', {}).get('active'):
                    context = current.values['_itinerary']
                    step = 'itinerary:' + context['stage']
                elif current and current.values.get('_discovery', {}).get('active'):
                    context = current.values['_discovery']
                    step = 'discovery:' + context['stage']
                elif current and current.values.get('_bus', {}).get('active'):
                    context = current.values['_bus']
                    step = 'bus:' + context['stage']
                text = self.interpreter(text, step, today, context)
            except Exception:
                # Natural-language interpretation is optional; deterministic parsing remains available.
                pass
        command = clean(text)
        if current:
            current.values.pop('_capabilities', None)
            current.values.pop('_preference_actions', None)
        if command in {
            'menu', 'recursos', 'quais recursos', 'me mostre o menu',
            'o que voce faz', 'o que vc faz', 'oq vc faz',
            'o que voce pode fazer', 'o que vc pode fazer',
            'o que da pra fazer', 'oq da pra fazer',
            'como voce pode me ajudar', 'como vc pode me ajudar',
            'como pode me ajudar', 'como vc me ajuda',
        }:
            session = self.sessions.setdefault(user_id, Session())
            if session.values.get('_discovery'):
                session.values['_discovery']['active'] = False
            if session.values.get('_itinerary'):
                session.values['_itinerary']['active'] = False
            if session.values.get('_bus'):
                session.values['_bus']['active'] = False
            session.values['_capabilities'] = True
            return ('*O que você quer planejar?* ✈️\n\n'
                    '*Passagens*\n'
                    'Compare voos de ida e volta por preço, duração, paradas e orçamento.\n\n'
                    '*Ônibus*\n'
                    'Prepare uma busca rodoviária; tarifas ao vivo dependem do credenciamento da fonte.\n\n'
                    '*Mais possibilidades*\n'
                    'Veja datas próximas ou compare até 3 destinos escolhidos por você.\n\n'
                    '*Passeios*\n'
                    'Monte de 1 a 3 dias em São Paulo, Bogotá ou Rio de Janeiro.\n\n'
                    '*Organização*\n'
                    'Veja o resumo e um checklist da sua viagem.\n\n'
                    '*Suas preferências*\n'
                    'Salve origem, passageiros e o tipo de oferta que prefere.\n\n'
                    'Abra o menu abaixo para escolher por onde começar.')
        if command in FAQ_RESPONSES:
            return FAQ_RESPONSES[command]
        if command in {'resumo da viagem', 'resumo viagem'}:
            return trip_summary(self.sessions.get(user_id, Session()))
        if command in {'checklist da viagem', 'checklist viagem'}:
            return travel_checklist(self.sessions.get(user_id, Session()))
        if command in {'voos', 'consultar voos', 'voltar aos voos', 'sair do roteiro'}:
            session = self.sessions.setdefault(user_id, Session())
            if session.values.get('_discovery'):
                session.values['_discovery']['active'] = False
            if session.values.get('_itinerary'):
                session.values['_itinerary']['active'] = False
            if session.values.get('_bus'):
                session.values['_bus']['active'] = False
            return self.resume_flights(session)
        if clean(text) not in {'cancelar', '/cancelar', '/start'}:
            from .buses import handle as handle_bus
            session = self.sessions.get(user_id, Session())
            bus_reply = handle_bus(session, text, today, self.bus_search, self.on_search)
            if bus_reply is not None:
                if session.values.get('_discovery'):
                    session.values['_discovery']['active'] = False
                if session.values.get('_itinerary'):
                    session.values['_itinerary']['active'] = False
                self.sessions[user_id] = session
                return bus_reply
            from .itinerary import START as ITINERARY_START
            import re
            itinerary_command = command in ITINERARY_START | {'meu roteiro', 'fontes do roteiro', 'ajustar roteiro', 'apagar roteiro'} or re.fullmatch(r'(?:quero (?:um |montar um )?)?roteiro (?:para|em|pra) .+', command)
            if itinerary_command and current and current.values.get('_discovery'):
                current.values['_discovery']['active'] = False
            if itinerary_command and current and current.values.get('_bus'):
                current.values['_bus']['active'] = False
            from .discovery import handle as discover
            session = self.sessions.get(user_id, Session())
            discovery_reply = discover(session, text, today, self.flight_search, self.on_search)
            if discovery_reply is not None:
                self.sessions[user_id] = session
                return discovery_reply
            from .itinerary import handle
            session = self.sessions.get(user_id, Session())
            itinerary_reply = handle(session, text, today)
            if itinerary_reply is not None:
                self.sessions[user_id] = session
                return itinerary_reply
        if self.flight_search is not None:
            return self.live_reply(user_id, text, today)
        if not text:
            return "Envie uma mensagem de texto para continuar."
        if text.casefold() in {"cancelar", "/cancelar", "/start"}:
            self.sessions.pop(user_id, None)
        if user_id not in self.sessions:
            self.sessions[user_id] = Session()
            return (
                "Olá! Sou o Atlas. Este é um simulador sem tarifas reais. "
                "Vamos planejar uma ida e volta. De qual cidade ou aeroporto você sai?"
            )
        session = self.sessions[user_id]
        if session.step == "complete":
            return "Digite cancelar para iniciar outra viagem. A busca real ainda não está conectada."
        if session.step in {"origin", "destination"}:
            if len(text) < 2 or len(text) > 100:
                return "Informe uma cidade ou aeroporto com 2 a 100 caracteres."
            if session.step == "destination" and text.casefold() == session.values["origin"].casefold():
                return "O destino deve ser diferente da origem. Para onde você quer ir?"
        if session.step in {"departure", "return"}:
            try:
                parsed = datetime.strptime(text, "%d/%m/%Y").date()
            except ValueError:
                return "Informe uma data válida no formato DD/MM/AAAA."
            if parsed < today:
                return "A data não pode estar no passado. Informe outra data."
            if session.step == "return":
                departure = datetime.strptime(session.values["departure"], "%d/%m/%Y").date()
                if parsed < departure:
                    return "A volta não pode ser anterior à ida. Informe outra data."
            text = parsed.strftime("%d/%m/%Y")
        if session.step == "priority":
            labels = {"1": "menor preço", "2": "menor duração", "3": "sem paradas"}
            if text not in labels:
                return "Escolha 1 para menor preço, 2 para menor duração ou 3 para sem paradas."
            session.values["priority"] = labels[text]
            session.step = "complete"
            values = session.values
            return (
                f"Resumo: {values['origin']} → {values['destination']}; "
                f"ida {values['departure']}, volta {values['return']}; "
                f"escolha: {values['priority']}. "
                "Não realizei uma busca: o fornecedor ainda não está conectado. "
                "Digite cancelar para recomeçar."
            )
        transitions = {
            "origin": ("destination", "Para onde você quer ir?"),
            "destination": ("departure", "Qual é a data de ida? Use DD/MM/AAAA."),
            "departure": ("return", "Qual é a data de volta? Use DD/MM/AAAA."),
            "return": ("priority", OFFLINE_PRIORITY_PROMPT),
        }
        session.values[session.step] = text
        session.step, response = transitions[session.step]
        return response

    def live_reply(self, user_id, text, today):
        from .flights import resolve_airport, format_results, rank
        command = clean(text)
        choices = PRIORITY_PROMPT
        if command in {"cancelar", "/cancelar", "/start"}:
            self.sessions.pop(user_id, None)
        fresh = user_id not in self.sessions
        if fresh:
            self.sessions[user_id] = Session()
        session = self.sessions[user_id]
        values = session.values
        from .preferences import FIELDS, describe
        if command == 'salvar preferencias':
            if not all(key in values for key in FIELDS):
                return 'Primeiro informe origem, quantidade de adultos e preferência de busca. Depois digite salvar preferências.'
            self.preferences.save(user_id, values)
            values['_preference_actions'] = True
            return ('*Preferências salvas*\n\n' + describe(values) +
                    '\n\nDestino, datas e orçamento não fazem parte desse perfil.\n\n'
                    '*O que você quer fazer?*\nAbra as opções abaixo ou digite usar preferências para aplicar.')
        if command in {'preferencias', 'minhas preferencias'}:
            saved = self.preferences.load(user_id)
            if saved:
                values['_preference_actions'] = True
            return ('*Suas preferências*\n\n' + describe(saved) +
                    '\n\nAbra as opções abaixo para aplicar, atualizar ou remover esse perfil.'
                    if saved else 'Você ainda não salvou preferências. Após informar origem, adultos e preferência de busca, digite salvar preferências.')
        if command == 'apagar preferencias':
            self.preferences.delete(user_id)
            return 'Preferências removidas. Os dados da conversa e da viagem atual permanecem; essa ação apaga apenas as preferências salvas.'
        if command == 'usar preferencias':
            saved = self.preferences.load(user_id)
            if not saved:
                return 'Você ainda não salvou preferências. Podemos continuar com os dados da viagem atual.'
            return '*Preferências aplicadas*\n\n' + describe(saved) + '\n\n' + self.apply_trip_fields(session, saved, today)
        if command in {'datas flexiveis', 'datas proximas', 'flexibilidade'} and session.step != 'flexibility':
            session.step = 'flexibility'
            return FLEXIBILITY_PROMPT
        if session.step == 'flexibility':
            options = {'datas proximas': 'nearby', '1': 'nearby', 'datas exatas': 'exact', '2': 'exact'}
            options.update({'comparar 1 dia': 'nearby', 'manter datas': 'exact'})
            if command not in options:
                return FLEXIBILITY_PROMPT
            values['flexibility'] = options[command]
            for key in ('result', '_choices', '_budget_refine', '_price_question'):
                values.pop(key, None)
            return self.next_question(session)
        from .trip_input import extract_trip
        import re
        if re.search(r'\b(?:onibus|rodoviari[oa])\b', command):
            return 'A fonte de ônibus ainda não está credenciada. Não alterei sua viagem nem consultei voos no lugar de ônibus. Digite ônibus para ver o estado dessa integração.'
        if re.search(r'\b(?:criancas?|bebes?)\b', command) or re.search(r'-\s*\d+\s+adult', command):
            return 'Nesta versão, a busca atende apenas de 1 a 6 adultos. Não alterei os dados da viagem.'
        try:
            fields = extract_trip(text)
        except ValueError as error:
            return str(error)
        if set(fields) == {'budget'} and session.step in {'budget', 'complete'}:
            text = fields['budget']
            fields = {}
            if session.step == 'complete':
                values['_budget_refine'] = True
                session.step = 'budget'
        if fields:
            return self.apply_trip_fields(session, fields, today)
        if fresh and command != 'ajuda':
            saved_hint = ' Você tem preferências salvas; digite usar preferências para reutilizar.' if self.preferences.load(user_id) else ''
            return "Olá! Sou o *Atlas*. ✈️\n\nPosso comparar voos de ida e volta e ajudar a planejar seus passeios.\n\n*De qual cidade ou aeroporto você sai?*\nPode enviar origem, destino, datas e adultos juntos.\n\nDigite *menu* para explorar os recursos." + saved_hint
        text = choice(text, session.step)
        if command == "ajuda":
            return ("*Como posso ajudar*\n\n"
                    "✈️ *Passagens*\nIda e volta para 1 a 6 adultos. Compare preço, duração e paradas.\n\n"
                    "🚌 *Ônibus*\nDigite ônibus para iniciar; preços reais só aparecem quando a fonte parceira estiver credenciada.\n\n"
                    "*Quer gastar menos?*\nUse orçamento, datas flexíveis (±1 dia) ou explorar destinos (até 3 aeroportos).\n\n"
                    "*Passeios*\nDigite roteiro para planejar de 1 a 3 dias em São Paulo, Bogotá ou Rio de Janeiro.\n\n"
                    "*Organização*\nUse resumo da viagem ou checklist da viagem para reunir o plano e revisar preparativos.\n\n"
                    "*Suas preferências*\nSalvar preferências, minhas preferências, usar preferências ou apagar preferências.\n\n"
                    "*Depois da busca*\n"
                    "• Abra uma oferta ou altere os critérios.\n"
                    "• Compare datas próximas se o preço estiver alto.\n"
                    "• Monte um roteiro de passeios para o destino.\n\n"
                    "Digite menu para ver as opções ou cancelar para outra viagem. Ônibus e busca por mês inteiro ainda não estão disponíveis.")
        if session.step == "complete":
            if command in {'carinho em', 'carinho hein', 'caro hein', 'caro em'}:
                values['_price_question'] = True
                return 'Você achou o preço alto? Responda sim para ajustar o orçamento ou diga o que gostaria de mudar.'
            price_question = values.pop('_price_question', False)
            if command in {'orcamento', 'alterar orcamento', 'ta caro', 'esta caro', 'muito caro', 'achei caro', 'achei bem caro', 'ficou caro', 'caro demais', 'achei mais caro', 'ficou mais caro', 'ta mais caro', 'esta mais caro'} or (price_question and command in {'sim', 'isso', 'isso mesmo'}):
                values['_budget_refine'] = True
                session.step = 'budget'
                return BUDGET_PROMPT
            if "adults" not in values:
                session.step = "adults"
                return "Atualizei o Atlas com busca de voos. Quantos adultos vão viajar? De 1 a 6."
            if command in {'ofertas', 'opcoes', 'ver ofertas'}:
                return format_results(values.get('result', {'status': 'empty'}), values)
            if command in {'recomendar oferta', 'comparar ofertas'}:
                offers = rank(values.get('result', {}).get('offers', []), values['priority'], values.get('budget'))
                if not offers:
                    return 'Não tenho ofertas válidas salvas para comparar. Digite buscar para consultar novamente.'
                priority = {'1': 'menor preço', '2': 'menor duração', '3': 'voo sem paradas',
                            '4': 'maior preço entre as opções retornadas'}[values['priority']]
                if command == 'recomendar oferta':
                    offer = offers[0]
                    duration = offer['duration']
                    return (f"*Minha sugestão pelos seus critérios*\n\nA oferta 1 aparece primeiro por priorizar *{priority}*.\n\n"
                            f"• Total: R$ {money(offer['price'])}\n"
                            f"• Duração somada: {duration // 60}h{duration % 60:02}\n"
                            f"• Até {offer['stops']} parada(s) por sentido\n\n"
                            "Isso não confirma conforto, bagagem ou regras tarifárias. Digite *link 1* para conferir na fonte.")
                lines = ['*Comparação das ofertas salvas*', '', f'Ordenação atual: {priority}.']
                for index, offer in enumerate(offers, 1):
                    duration = offer['duration']
                    lines.append(f"\n*{index}.* R$ {money(offer['price'])} • {duration // 60}h{duration % 60:02} • até {offer['stops']} parada(s)")
                lines.append('\nDigite *recomendar oferta* para entender a primeira opção ou *link 1* para abrir uma tarifa.')
                return '\n'.join(lines)
            if command.startswith("link "):
                offers = rank(values.get("result", {}).get("offers", []), values["priority"], values.get('budget'))
                try:
                    index = int(command.split()[1]) - 1
                    if index < 0 or index >= len(offers):
                        raise ValueError
                    url = offers[index].get("url")
                    warning = (f"Ao abrir, confirme que o Google Flights mostra {values['adults']} adultos antes de continuar. "
                               if int(values['adults']) > 1 else '')
                    return (warning + "Confira disponibilidade e valor final no Google Flights:\n" + url) if url else "O fornecedor não retornou um link para essa oferta. Digite buscar para atualizar."
                except (ValueError, IndexError):
                    return "Use link seguido do número de uma oferta exibida, por exemplo: link 1."
            transitions = {"filtros": ("priority", choices), "datas": ("departure", "Qual é a nova data de ida? DD/MM/AAAA."), "passageiros": ("adults", "Quantos adultos? De 1 a 6.")}
            if command in transitions:
                values.pop("result", None)
                if command == 'datas':
                    values.pop('departure', None)
                    values.pop('return', None)
                session.step, answer = transitions[command]
                return answer
            if command == "buscar":
                session.step = "confirm"
            else:
                return ("*O que você quer fazer?*\n\n"
                        "• Digite *link 1* para abrir uma oferta.\n"
                        "• Use *filtros*, *datas*, *passageiros* ou *orçamento* para ajustar.\n"
                        "• Digite *buscar* para atualizar os preços.\n"
                        "• Digite *cancelar* para começar outra viagem.")
        if session.step == "confirm":
            if not is_confirmation(text) and command != "buscar":
                return "Digite sim para consultar ou cancelar para recomeçar."
            if datetime.strptime(values["departure"], "%d/%m/%Y").date() < today:
                session.step = "departure"
                return "A data de ida passou. Informe uma nova data em DD/MM/AAAA."
            if self.on_search:
                self.on_search('Estou consultando as opções para sua viagem. A busca pode levar até um minuto.')
            request = {k: v for k, v in values.items() if k != "result" and not k.startswith('_')}
            if values.get('flexibility') == 'nearby':
                from .flexible import search_nearby
                result = search_nearby(self.flight_search, request, today)
            else:
                result = self.flight_search(request)
            values["result"] = result
            session.step = "complete"
            return format_results(result, values)
        if session.step in {"origin", "destination"}:
            import re
            text = re.sub(r'^(?:(?:eu )?(?:saio|vou sair|quero sair) de|(?:eu )?quero ir (?:para|pra)|(?:vou )?(?:para|pra))\s+', '', clean(text))
            code, error = resolve_airport(text)
            if error:
                return error
            if session.step == "destination" and code == values.get("origin"):
                return "Escolha um aeroporto diferente da origem."
            text = code
        if session.step in {"departure", "return"}:
            try:
                departure = datetime.strptime(values['departure'], '%d/%m/%Y').date() if session.step == 'return' else None
                parsed = parse_date(text, today, departure)
            except ValueError:
                return 'Não consegui entender essa data. Pode escrever "23/10/2026", "dia 23 de outubro desse ano" ou "amanhã". Inclua o mês se disser só o dia.'
            if parsed < today:
                return "A data não pode estar no passado."
            if session.step == "return" and parsed < datetime.strptime(values["departure"], "%d/%m/%Y").date():
                return "A volta não pode ser anterior à ida."
            text = parsed.strftime("%d/%m/%Y")
        if session.step == "adults" and text not in {str(i) for i in range(1, 7)}:
            return "Nesta versão, informe de 1 a 6 adultos. Crianças e bebês ainda não são atendidos."
        if session.step == "priority" and text not in {"1", "2", "3", "4"}:
            return choices
        if session.step == 'budget':
            try:
                text = parse_budget(text)
            except ValueError:
                return 'Não consegui interpretar o total. ' + BUDGET_PROMPT
            if values.pop('_budget_refine', False):
                values['budget'] = text
                session.step = 'complete'
                return 'Apliquei o orçamento às ofertas da consulta anterior. Use buscar para atualizar os preços.\n' + format_results(values.get('result', {'status': 'empty'}), values)
        transitions = {
            "origin": ("destination", f"Origem: {text}. Para qual cidade ou aeroporto você vai?"),
            "destination": ("departure", f'Destino: {text}. Qual é a data de ida? Pode escrever "dia 23 de outubro desse ano" ou DD/MM/AAAA.'),
            "departure": ("return", f"Entendi a ida em {text}. Qual é a data de volta? Pode usar uma data ou '7 dias depois'."),
            "return": ("adults", "Quantos adultos? De 1 a 6."),
            "adults": ("priority", choices),
            "priority": ("budget", BUDGET_PROMPT),
            "budget": ("confirm", ""),
        }
        values[session.step] = text
        session.step, answer = transitions[session.step]
        # Explicit multi-field requests can already contain later answers.
        if session.step in values:
            return self.next_question(session)
        if session.step == "confirm":
            return self.next_question(session)
        return answer

    def next_question(self, session):
        values = session.values
        prompts = {
            'origin': 'De qual cidade ou aeroporto você sai?',
            'destination': 'Para qual cidade ou aeroporto você vai?',
            'departure': 'Qual é a data de ida? Informe dia, mês e ano; a busca por mês inteiro ainda não está disponível.',
            'return': "Qual é a data de volta? Pode usar uma data ou '7 dias depois'.",
            'adults': 'Quantos adultos? De 1 a 6.',
            'priority': PRIORITY_PROMPT,
            'budget': BUDGET_PROMPT,
        }
        for key, prompt in prompts.items():
            if key not in values:
                session.step = key
                return prompt
        session.step = 'confirm'
        from .flexible import label as flexibility_label
        priority = {'1': 'Menor preço', '2': 'Menor duração', '3': 'Sem paradas', '4': 'Maior preço entre as ofertas encontradas'}[values['priority']]
        return (f"*Confirmar busca: {values['origin']} → {values['destination']}*\n\n"
                f"• Ida: {values['departure']}\n• Volta: {values['return']}\n"
                f"• Passageiros: {values['adults']} adulto(s)\n• Classe: econômica\n"
                f"• Preferência: {priority}\n\n{label(values.get('budget'))}.\n"
                f"{flexibility_label(values)}\n\n*Posso buscar?*\nEscolha confirmar ou informe o que deseja alterar.")

    def resume_flights(self, session):
        """Resume the pending question without querying or changing flight criteria."""
        if session.step == 'complete':
            if self.flight_search is None:
                return 'Você está no simulador de voos. Digite cancelar para uma nova viagem ou roteiro para passeios.'
            from .flights import format_results
            return format_results(session.values.get('result', {'status': 'empty'}), session.values)
        prompts = {
            'origin': 'De qual cidade ou aeroporto você sai?',
            'destination': 'Para qual cidade ou aeroporto você vai?',
            'departure': 'Qual é a data de ida?',
            'return': 'Qual é a data de volta?',
            'adults': 'Quantos adultos? De 1 a 6.',
            'priority': PRIORITY_PROMPT,
            'budget': BUDGET_PROMPT,
            'flexibility': FLEXIBILITY_PROMPT,
        }
        if session.step == 'confirm':
            return self.next_question(session)
        return 'Vamos continuar sua busca de passagens. ' + prompts.get(session.step, 'Digite cancelar para recomeçar.')

    def apply_trip_fields(self, session, fields, today):
        """Keep valid explicit fields, ask about invalid ones, and invalidate old fares."""
        from .flights import resolve_airport
        values = session.values
        errors = []
        # No previously quoted fare may be attached to a changed itinerary.
        for key in ('result', '_choices', '_budget_refine', '_price_question'):
            values.pop(key, None)
        if 'departure' in fields and 'return' not in fields:
            values.pop('return', None)
        for key in ('origin', 'destination', 'departure', 'return', 'adults', 'priority', 'budget'):
            if key not in fields:
                continue
            raw = fields[key]
            error = None
            parsed = raw
            if key in {'origin', 'destination'}:
                parsed, error = resolve_airport(raw)
            elif key in {'departure', 'return'}:
                try:
                    departure = datetime.strptime(values['departure'], '%d/%m/%Y').date() if key == 'return' and 'departure' in values else None
                    parsed_date = parse_date(raw, today, departure)
                    if parsed_date < today:
                        raise ValueError()
                    parsed = parsed_date.strftime('%d/%m/%Y')
                except ValueError:
                    error = 'Informe uma data completa e futura para a ' + ('ida' if key == 'departure' else 'volta') + '. Não escolhi dias automaticamente; a busca por mês inteiro ainda não está disponível.'
            elif key in {'adults', 'priority'}:
                parsed = choice(raw, key)
                if parsed not in ({str(i) for i in range(1, 7)} if key == 'adults' else {'1', '2', '3', '4'}):
                    error = 'Informe de 1 a 6 adultos.' if key == 'adults' else 'Escolha menor preço, menor duração, sem paradas ou maior preço.'
            elif key == 'budget':
                try:
                    parsed = parse_budget(raw)
                except ValueError:
                    error = BUDGET_PROMPT
            if error:
                values.pop(key, None)
                errors.append((key, error))
            else:
                values[key] = parsed
        if values.get('origin') and values.get('origin') == values.get('destination'):
            values.pop('destination', None)
            errors.append(('destination', 'Escolha um aeroporto diferente da origem.'))
        if values.get('departure') and values.get('return'):
            if datetime.strptime(values['return'], '%d/%m/%Y') < datetime.strptime(values['departure'], '%d/%m/%Y'):
                values.pop('return', None)
                errors.append(('return', 'A volta não pode ser anterior à ida. Qual é a nova data de volta?'))
        if errors:
            session.step = errors[0][0]
            return errors[0][1] + ' Guardei os outros dados válidos da viagem.'
        return self.next_question(session)
