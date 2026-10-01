import io
import json
import unittest
from datetime import date

from atlas.conversation import Conversation
from atlas.nlu import ENDPOINT, interpret, needs_interpretation
from atlas.trip_input import extract_trip


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def answer(intent, value="", confidence=0.99):
    payload = {"choices": [{"message": {"content": json.dumps({
        "intent": intent, "answer": value, "confidence": confidence,
    })}}]}
    return Response(json.dumps(payload).encode())


class NluTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ATLAS_NLU_ENABLED": "true",
            "GROQ_API_KEY": "secret-test-value",
            "GROQ_MODEL": "openai/gpt-oss-20b",
        }
        self.today = date(2026, 9, 25)

    def call(self, text, response, step="origin"):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return response

        result = interpret(text, step, self.today, {}, self.config, opener=opener)
        return result, captured

    def test_maps_only_allowlisted_command_with_strict_schema(self):
        result, captured = self.call("como que vc consegue me ajudar?", answer("menu"))
        self.assertEqual(result, "menu")
        self.assertEqual(captured["request"].full_url, ENDPOINT)
        self.assertEqual(captured["timeout"], 6)
        request = json.loads(captured["request"].data)
        self.assertTrue(request["response_format"]["json_schema"]["strict"])
        self.assertFalse(request["response_format"]["json_schema"]["schema"]["additionalProperties"])
        self.assertNotIn("secret-test-value", request["messages"][0]["content"])

    def test_ignores_model_copy_for_an_allowlisted_command(self):
        result, _ = self.call(
            'qual dessas passagens eu deveria escolher?',
            answer('offer_recommendation', 'I would choose option 99'),
            'complete',
        )
        self.assertEqual(result, 'recomendar oferta')

    def test_maps_itinerary_commands_without_model_written_copy(self):
        mappings = (
            ("queria ver de onde vieram essas informacoes", "itinerary_sources", "fontes do roteiro"),
            ("quero mudar algumas coisas no passeio", "itinerary_edit", "ajustar roteiro"),
            ("mostra o passeio que voce montou", "itinerary_show", "meu roteiro"),
        )
        for text, intent, expected in mappings:
            with self.subTest(intent=intent):
                result, _ = self.call(text, answer(intent), "itinerary:done")
                self.assertEqual(result, expected)

        result, _ = self.call(
            "apaga tudo talvez", answer("itinerary_delete", "confirmado"), "itinerary:done")
        self.assertEqual(result, "apaga tudo talvez")
        result, _ = self.call(
            "nao apaga meu roteiro", answer("itinerary_delete"), "itinerary:done")
        self.assertEqual(result, "nao apaga meu roteiro")
        result, _ = self.call(
            "por favor, apaga meu roteiro", answer("itinerary_delete"), "itinerary:done")
        self.assertEqual(result, "apagar roteiro")

    def test_maps_offer_guidance_and_faqs_to_controlled_commands(self):
        mappings = (
            ('qual dessas passagens voce escolheria?', 'offer_recommendation', 'recomendar oferta'),
            ('me explica a diferenca entre elas', 'offer_comparison', 'comparar ofertas'),
            ('essa tarifa inclui mala despachada?', 'faq_baggage', 'duvida bagagem'),
            ('eu pago a passagem para voce?', 'faq_purchase', 'duvida compra'),
            ('esse valor fica garantido?', 'faq_prices', 'duvida precos'),
            ('o que voces mandam para a inteligencia artificial?', 'faq_privacy', 'duvida privacidade'),
            ('voce tambem pesquisa passagem de onibus?', 'faq_bus', 'duvida onibus'),
            ('da para me avisar quando o preco baixar?', 'faq_alerts', 'duvida alertas'),
            ('quais lugares e viagens voce atende hoje?', 'faq_scope', 'duvida cobertura'),
            ('qual opcao tem o assento mais confortavel?', 'faq_comfort', 'duvida conforto'),
            ('valeu demais pela ajuda', 'gratitude', 'obrigado atlas'),
            ('junta tudo que ja planejei', 'trip_summary', 'resumo da viagem'),
            ('o que eu preciso conferir antes de viajar?', 'travel_checklist', 'checklist da viagem'),
        )
        for text, intent, expected in mappings:
            with self.subTest(intent=intent):
                result, _ = self.call(text, answer(intent), 'complete')
                self.assertEqual(result, expected)

    def test_distinguishes_bus_capability_question_from_search_request(self):
        result, _ = self.call('preciso me deslocar pela estrada e queria uma passagem', answer('bus_search'))
        self.assertEqual(result, 'onibus')
        result, _ = self.call('voce tambem pesquisa passagem rodoviaria?', answer('faq_bus'))
        self.assertEqual(result, 'duvida onibus')

    def test_questions_with_para_are_not_mistaken_for_routes(self):
        self.assertEqual(extract_trip('eu pago a passagem para voce?'), {})
        self.assertEqual(
            extract_trip('o que voces mandam para a inteligencia artificial?'), {})

    def test_accepts_valid_step_answer(self):
        result, _ = self.call("eu parto lá de Confins", answer("step_answer", "Confins"))
        self.assertEqual(result, "Confins")

    def test_extracts_two_explicit_places_without_inventing_airports(self):
        phrase = 'meu embarque acontece em Confins e meu destino vai ser San Andrés'
        result, _ = self.call(phrase, answer('trip_route', 'Confins -> San Andrés'))
        self.assertEqual(result, 'Confins -> San Andrés')
        result, _ = self.call(phrase, answer('trip_route', 'Confins -> Bogotá'))
        self.assertEqual(result, phrase)
        result, _ = self.call(phrase, answer('trip_route', 'CNF -> ADZ'), 'departure')
        self.assertEqual(result, phrase)

    def test_rejects_invalid_or_out_of_context_answer(self):
        result, _ = self.call("somos oito", answer("step_answer", "8"), "adults")
        self.assertEqual(result, "somos oito")
        result, _ = self.call("mude tudo", answer("step_answer", "GRU"), "complete")
        self.assertEqual(result, "mude tudo")

    def test_low_confidence_and_errors_fall_back(self):
        result, _ = self.call("talvez faça algo", answer("itinerary", confidence=0.70))
        self.assertEqual(result, "talvez faça algo")
        result, _ = self.call("qualquer coisa", Response(b"not-json"))
        self.assertEqual(result, "qualquer coisa")

    def test_lower_threshold_is_limited_to_informational_intents(self):
        result, _ = self.call('me explica a bagagem', answer('faq_baggage', confidence=0.85))
        self.assertEqual(result, 'duvida bagagem')
        result, _ = self.call('cancela isso', answer('cancel', confidence=0.85))
        self.assertEqual(result, 'cancela isso')

    def test_strips_safe_place_prefix_from_step_answer(self):
        result, _ = self.call('eu embarco la pelo aeroporto de Confins',
                              answer('step_answer', 'aeroporto de Confins', confidence=0.85))
        self.assertEqual(result, 'Confins')
        result, _ = self.call('quero sair algum dia',
                              answer('step_answer', 'amanha', confidence=0.85), 'departure')
        self.assertEqual(result, 'quero sair algum dia')

    def test_disabled_interpreter_does_not_call_network(self):
        def fail(*args, **kwargs):
            raise AssertionError("network should not be called")

        config = dict(self.config, ATLAS_NLU_ENABLED="false")
        self.assertEqual(interpret("oi", "origin", self.today, {}, config, opener=fail), "oi")

    def test_locally_understood_inputs_do_not_spend_quota(self):
        self.assertFalse(needs_interpretation("Confins", "origin", self.today, {}))
        self.assertFalse(needs_interpretation("como vc pode me ajudar", "origin", self.today, {}))
        self.assertFalse(needs_interpretation("dia 23 de outubro desse ano", "departure", self.today, {}))
        self.assertFalse(needs_interpretation("duas pessoas", "adults", self.today, {}))
        self.assertFalse(needs_interpretation("a mais barata", "priority", self.today, {}))
        candidates = {"origin": "CNF"}
        self.assertFalse(needs_interpretation(
            "GRU, BOG, REC", "discovery:candidates", self.today, candidates))
        self.assertFalse(needs_interpretation(
            "quero comparar Guarulhos, Recife e Bogota", "discovery:candidates", self.today, candidates))
        self.assertTrue(needs_interpretation("eu parto la de Confins", "origin", self.today, {}))
        self.assertFalse(needs_interpretation(
            'saio de Confins e quero ir para San Andrés na Colômbia', 'origin', self.today, {}))

    def test_conversation_uses_interpreted_command(self):
        bot = Conversation(interpreter=lambda *args: "menu")
        reply = bot.reply("user", "me conta o que rola", today=self.today)
        self.assertIn("O que você quer planejar", reply)

    def test_conversation_passes_active_overlay_stage(self):
        calls = []

        def interpreter(text, step, today, values):
            calls.append((text, step))
            return "2" if step == "itinerary:days" else text

        bot = Conversation(interpreter=interpreter)
        for text in ("roteiro", "Sao Paulo", "sem data"):
            bot.reply("user", text, today=self.today)
        reply = bot.reply("user", "quero aproveitar dois dias", today=self.today)
        self.assertIn(("quero aproveitar dois dias", "itinerary:days"), calls)
        self.assertIn("cultura", reply)

    def test_overlay_answers_are_strictly_bounded(self):
        result, _ = self.call("quero bastante tempo", answer("step_answer", "5"), "itinerary:days")
        self.assertEqual(result, "quero bastante tempo")
        result, _ = self.call("quero arte e museus", answer("step_answer", "cultura"), "itinerary:interest")
        self.assertEqual(result, "cultura")
        result, _ = self.call("quero conhecer a cidade maravilhosa",
                              answer("step_answer", "rio de janeiro"), "itinerary:city")
        self.assertEqual(result, "rio de janeiro")
        result, _ = self.call("escolho a segunda", answer("step_answer", "destino 2"), "discovery:done")
        self.assertEqual(result, "destino 2")
        result, _ = self.call("pode colocar qualquer um", answer("step_answer", "destino 4"), "discovery:done")
        self.assertEqual(result, "pode colocar qualquer um")
        result, _ = self.call(
            "quero comparar tres lugares", answer("step_answer", "GRU, BOG, REC, SSA"),
            "discovery:candidates")
        self.assertEqual(result, "quero comparar tres lugares")
        result, _ = self.call('quero o mais confortavel', answer('step_answer', '4'), 'bus:priority')
        self.assertEqual(result, '4')
        result, _ = self.call('somos nove', answer('step_answer', '9'), 'bus:adults')
        self.assertEqual(result, 'somos nove')


if __name__ == "__main__":
    unittest.main()
