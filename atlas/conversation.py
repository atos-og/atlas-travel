"""Channel-independent guided travel conversation with optional live search."""

from dataclasses import dataclass, field
from datetime import date, datetime
from .language import local_today, parse_date, choice, clean
from .budget import parse_budget, BUDGET_PROMPT, label


@dataclass
class Session:
    step: str = "origin"
    values: dict = field(default_factory=dict)


class Conversation:
    def __init__(self, flight_search=None, on_search=None, preferences=None):
        self.sessions: dict[str, Session] = {}
        self.flight_search = flight_search
        self.on_search = on_search
        from .preferences import Preferences
        self.preferences = preferences if preferences is not None else Preferences()

    def reply(self, user_id: str, text: str, *, today: date | None = None) -> str:
        text = text.strip()
        today = today or local_today()
        command = clean(text)
        current = self.sessions.get(user_id)
        if current:
            current.values.pop('_capabilities', None)
        if command in {'menu', 'recursos', 'o que voce faz', 'o que voce pode fazer'}:
            session = self.sessions.setdefault(user_id, Session())
            if session.values.get('_discovery'):
                session.values['_discovery']['active'] = False
            if session.values.get('_itinerary'):
                session.values['_itinerary']['active'] = False
            session.values['_capabilities'] = True
            return ('Como posso ajudar na sua viagem?\n'
                    '• Voos: ida e volta, preço, duração, paradas e orçamento.\n'
                    '• Datas próximas: comparar até 3 combinações em ±1 dia.\n'
                    '• Destinos por orçamento: comparar até 3 aeroportos escolhidos por você.\n'
                    '• Roteiro: 1 a 3 dias de passeios em São Paulo ou Bogotá.\n'
                    '• Preferências: salvar e reutilizar suas escolhas.\n'
                    'Escolha no menu ou escreva voos, roteiro, datas flexíveis ou minhas preferências.')
        if command in {'voos', 'consultar voos', 'voltar aos voos', 'sair do roteiro'}:
            session = self.sessions.setdefault(user_id, Session())
            if session.values.get('_discovery'):
                session.values['_discovery']['active'] = False
            if session.values.get('_itinerary'):
                session.values['_itinerary']['active'] = False
            return self.resume_flights(session)
        if clean(text) not in {'cancelar', '/cancelar', '/start'}:
            from .itinerary import START as ITINERARY_START
            import re
            itinerary_command = command in ITINERARY_START | {'meu roteiro', 'fontes do roteiro', 'ajustar roteiro', 'apagar roteiro'} or re.fullmatch(r'(?:quero (?:um |montar um )?)?roteiro (?:para|em|pra) .+', command)
            if itinerary_command and current and current.values.get('_discovery'):
                current.values['_discovery']['active'] = False
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
            "return": ("priority", "Escolha: 1 — menor preço; 2 — menor duração; 3 — sem paradas."),
        }
        session.values[session.step] = text
        session.step, response = transitions[session.step]
        return response

    def live_reply(self, user_id, text, today):
        from .flights import resolve_airport, format_results, rank
        command = clean(text)
        choices = "Escolha: 1 — menor preço; 2 — menor duração; 3 — sem paradas; 4 — maior preço entre as ofertas encontradas."
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
            return 'Preferências salvas: ' + describe(values) + ' Para reutilizar, digite usar preferências. Para remover, apagar preferências. Destino, datas e orçamento não foram salvos como preferências.'
        if command in {'preferencias', 'minhas preferencias'}:
            saved = self.preferences.load(user_id)
            return ('Preferências salvas: ' + describe(saved) + ' Digite usar preferências, salvar preferências para atualizar ou apagar preferências.'
                    if saved else 'Você ainda não salvou preferências. Após informar origem, adultos e preferência de busca, digite salvar preferências.')
        if command == 'apagar preferencias':
            self.preferences.delete(user_id)
            return 'Preferências removidas. Os dados da conversa e da viagem atual permanecem; essa ação apaga apenas as preferências salvas.'
        if command == 'usar preferencias':
            saved = self.preferences.load(user_id)
            if not saved:
                return 'Você ainda não salvou preferências. Podemos continuar com os dados da viagem atual.'
            return 'Apliquei suas preferências salvas. ' + self.apply_trip_fields(session, saved, today)
        if command in {'datas flexiveis', 'datas proximas', 'flexibilidade'} and session.step != 'flexibility':
            session.step = 'flexibility'
            return 'Posso comparar as datas originais com um dia antes e um dia depois, movendo ida e volta juntas e mantendo a estadia. São até 3 consultas, não o mês inteiro. Escolha datas próximas ou datas exatas.'
        if session.step == 'flexibility':
            options = {'datas proximas': 'nearby', '1': 'nearby', 'datas exatas': 'exact', '2': 'exact'}
            options.update({'comparar 1 dia': 'nearby', 'manter datas': 'exact'})
            if command not in options:
                return 'Escolha comparar 1 dia para variar ida e volta juntas, ou manter datas para datas exatas.'
            values['flexibility'] = options[command]
            for key in ('result', '_choices', '_budget_refine', '_price_question'):
                values.pop(key, None)
            return self.next_question(session)
        from .trip_input import extract_trip
        import re
        if re.search(r'\b(?:onibus|rodoviari[oa])\b', command):
            return 'A busca de ônibus ainda não está disponível. Não alterei sua viagem nem consultei voos no lugar de ônibus. Posso ajudar com passagens aéreas; digite ajuda para ver os recursos disponíveis.'
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
            return "Olá! Sou o Atlas. Posso consultar voos de ida e volta em classe econômica e comparar preço, duração e paradas. Também monto roteiros de passeios em São Paulo e Bogotá. De qual cidade ou aeroporto você sai? Pode enviar origem, destino, datas e adultos juntos. Digite menu para explorar os recursos." + saved_hint
        text = choice(text, session.step)
        if command == "ajuda":
            return "Disponível: voos de ida e volta, 1 a 6 adultos, orçamento total, comparação por preço/duração e filtro sem paradas. Digite datas flexíveis para comparar até 3 combinações, variando ida e volta juntas em 1 dia. Digite roteiro para planejar de 1 a 3 dias de passeios em São Paulo ou Bogotá, com fontes. Preferências: salvar preferências, minhas preferências, usar preferências ou apagar preferências. Após a busca: link 1, filtros, datas, passageiros, orçamento ou buscar. Cancelar inicia outra viagem. Em desenvolvimento: ônibus e busca por mês inteiro."
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
            if command.startswith("link "):
                offers = rank(values.get("result", {}).get("offers", []), values["priority"], values.get('budget'))
                try:
                    index = int(command.split()[1]) - 1
                    if index < 0 or index >= len(offers):
                        raise ValueError
                    url = offers[index].get("url")
                    return ("Confira disponibilidade e valor final no Google Flights:\n" + url) if url else "O fornecedor não retornou um link para essa oferta. Digite buscar para atualizar."
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
                return "Use link 1 para ver uma oferta; filtros, datas, passageiros ou orçamento para ajustar; buscar para atualizar; cancelar para outra viagem."
        if session.step == "confirm":
            if command not in {"sim", "s", "buscar", "confirmar", "pode buscar", "pode sim", "isso", "isso mesmo", "ok"}:
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
            'priority': 'Escolha: 1 — menor preço; 2 — menor duração; 3 — sem paradas; 4 — maior preço entre as ofertas encontradas.',
            'budget': BUDGET_PROMPT,
        }
        for key, prompt in prompts.items():
            if key not in values:
                session.step = key
                return prompt
        session.step = 'confirm'
        from .flexible import label as flexibility_label
        return (f"Confirmar busca: {values['origin']} → {values['destination']}, ida {values['departure']}, "
                f"volta {values['return']}, {values['adults']} adulto(s), econômica. Opção {values['priority']}; "
                f"{label(values.get('budget'))}. {flexibility_label(values)} Digite sim para consultar ou informe o que deseja alterar.")

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
            'priority': 'Escolha: 1 — menor preço; 2 — menor duração; 3 — sem paradas; 4 — maior preço entre as ofertas encontradas.',
            'budget': BUDGET_PROMPT,
            'flexibility': 'Escolha comparar 1 dia para variar ida e volta juntas, ou manter datas para datas exatas.',
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
