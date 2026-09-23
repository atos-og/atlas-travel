"""Local guided prototype. No external searches or messages."""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Session:
    step: str = "origin"
    values: dict[str, str] = field(default_factory=dict)


class Conversation:
    def __init__(self):
        self.sessions: dict[str, Session] = {}

    def reply(self, user_id: str, text: str, *, today: date | None = None) -> str:
        text = text.strip()
        today = today or date.today()
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
