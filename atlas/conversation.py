"""Local guided prototype. No external searches or messages."""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Session:
    step: str = "origin"
    values: dict[str, str] = field(default_factory=dict)


class Conversation:
    def __init__(self, flight_search=None):
        self.sessions: dict[str, Session] = {}
        self.flight_search = flight_search

    def reply(self, user_id: str, text: str, *, today: date | None = None) -> str:
        text = text.strip()
        today = today or date.today()
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
        command = text.casefold()
        choices = "Escolha: 1 — menor preço; 2 — menor duração; 3 — sem paradas; 4 — maior preço entre as ofertas encontradas."
        if command in {"cancelar", "/cancelar", "/start"}:
            self.sessions.pop(user_id, None)
        if user_id not in self.sessions:
            self.sessions[user_id] = Session()
            return "Olá! Sou o Atlas. Posso consultar voos de ida e volta em classe econômica e comparar preço, duração e paradas. De qual cidade ou aeroporto você sai? Digite ajuda para conhecer os recursos."
        session = self.sessions[user_id]
        values = session.values
        if command == "ajuda":
            return "Disponível: busca de voos de ida e volta, 1 a 6 adultos, comparação por preço/duração e filtro sem paradas. Após a busca: link 1, filtros, datas, passageiros ou buscar. Cancelar inicia outra viagem. Em desenvolvimento: ônibus, orçamento, roteiros e preferências."
        if session.step == "complete":
            if "adults" not in values:
                session.step = "adults"
                return "Atualizei o Atlas com busca de voos. Quantos adultos vão viajar? De 1 a 6."
            if command.startswith("link "):
                offers = rank(values.get("result", {}).get("offers", []), values["priority"])
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
                session.step, answer = transitions[command]
                return answer
            if command == "buscar":
                session.step = "confirm"
            else:
                return "Use link 1 para ver uma oferta; filtros, datas ou passageiros para ajustar; buscar para atualizar; cancelar para outra viagem."
        if session.step == "confirm":
            if command not in {"sim", "s", "buscar", "confirmar"}:
                return "Digite sim para consultar ou cancelar para recomeçar."
            if datetime.strptime(values["departure"], "%d/%m/%Y").date() < today:
                session.step = "departure"
                return "A data de ida passou. Informe uma nova data em DD/MM/AAAA."
            result = self.flight_search({k: v for k, v in values.items() if k != "result"})
            values["result"] = result
            session.step = "complete"
            return format_results(result, values)
        if session.step in {"origin", "destination"}:
            code, error = resolve_airport(text)
            if error:
                return error
            if session.step == "destination" and code == values.get("origin"):
                return "Escolha um aeroporto diferente da origem."
            text = code
        if session.step in {"departure", "return"}:
            try:
                parsed = datetime.strptime(text, "%d/%m/%Y").date()
            except ValueError:
                return "Informe uma data válida em DD/MM/AAAA."
            if parsed < today:
                return "A data não pode estar no passado."
            if session.step == "return" and parsed < datetime.strptime(values["departure"], "%d/%m/%Y").date():
                return "A volta não pode ser anterior à ida."
            text = parsed.strftime("%d/%m/%Y")
        if session.step == "adults" and text not in {str(i) for i in range(1, 7)}:
            return "Nesta versão, informe de 1 a 6 adultos. Crianças e bebês ainda não são atendidos."
        if session.step == "priority" and text not in {"1", "2", "3", "4"}:
            return choices
        transitions = {
            "origin": ("destination", f"Origem: {text}. Para qual cidade ou aeroporto você vai?"),
            "destination": ("departure", f"Destino: {text}. Qual é a data de ida? DD/MM/AAAA."),
            "departure": ("return", "Qual é a data de volta? DD/MM/AAAA."),
            "return": ("adults", "Quantos adultos? De 1 a 6."),
            "adults": ("priority", choices),
            "priority": ("confirm", ""),
        }
        values[session.step] = text
        session.step, answer = transitions[session.step]
        if session.step == "confirm":
            return (f"Confirmar busca: {values['origin']} → {values['destination']}, ida {values['departure']}, volta {values['return']}, {values['adults']} adulto(s), econômica. Opção {values['priority']}. Digite sim para consultar (pode levar até um minuto) ou cancelar.")
        return answer
