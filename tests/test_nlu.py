import io
import json
import unittest
from datetime import date

from atlas.conversation import Conversation
from atlas.nlu import ENDPOINT, interpret, needs_interpretation


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

    def test_accepts_valid_step_answer(self):
        result, _ = self.call("eu parto lá de Confins", answer("step_answer", "Confins"))
        self.assertEqual(result, "Confins")

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
        self.assertTrue(needs_interpretation("eu parto la de Confins", "origin", self.today, {}))

    def test_conversation_uses_interpreted_command(self):
        bot = Conversation(interpreter=lambda *args: "menu")
        reply = bot.reply("user", "me conta o que rola", today=self.today)
        self.assertIn("O que você quer planejar", reply)

    def test_conversation_does_not_interpret_active_overlay(self):
        calls = []
        bot = Conversation(interpreter=lambda text, *args: calls.append((text, *args)) or text)
        bot.reply("user", "roteiro", today=self.today)
        calls.clear()
        bot.reply("user", "Sao Paulo", today=self.today)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
