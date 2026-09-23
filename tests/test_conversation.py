import unittest
from datetime import date

from atlas.conversation import Conversation


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.bot = Conversation()

    def send(self, message, user="a"):
        return self.bot.reply(user, message, today=date(2026, 9, 23))

    def test_complete_flow_does_not_claim_live_search(self):
        for message in ["oi", "BH", "Bogotá", "12/11/2026", "19/11/2026"]:
            self.send(message)
        answer = self.send("3")
        self.assertIn("sem paradas", answer)
        self.assertIn("Não realizei uma busca", answer)
        self.assertNotIn("R$", answer)

    def test_dates_rejected_without_advancing(self):
        for message in ["oi", "BH", "Bogotá"]:
            self.send(message)
        self.assertIn("válida", self.send("31/02/2027"))
        self.assertIn("passado", self.send("01/01/2026"))
        self.send("12/11/2026")
        self.assertIn("anterior", self.send("11/11/2026"))
        self.assertEqual(self.bot.sessions["a"].step, "return")

    def test_users_have_independent_sessions(self):
        self.send("oi")
        self.send("BH")
        self.send("oi", user="b")
        self.assertEqual(self.bot.sessions["b"].values, {})
        self.assertEqual(self.bot.sessions["a"].values, {"origin": "BH"})

    def test_cancel_clears_trip(self):
        self.send("oi")
        self.send("BH")
        self.send("cancelar")
        self.assertEqual(self.bot.sessions["a"].values, {})
        self.assertEqual(self.bot.sessions["a"].step, "origin")


if __name__ == "__main__":
    unittest.main()
