import json
import unittest
from datetime import date
from unittest.mock import Mock

from atlas.conversation import Conversation, Session
from atlas.destinations import CITIES, PLACES, get_place
from atlas.itinerary import build_plan, render, sources
from atlas.interactive import payload_for


class PlanTests(unittest.TestCase):
    def test_all_supported_combinations_respect_caps_regions_and_interests(self):
        for city in CITIES:
            for days in range(1, 4):
                for interest in ('cultura', 'natureza', 'misto'):
                    for pace in ('tranquilo', 'equilibrado'):
                        plan = build_plan(city, days, interest, pace)
                        ids = [pid for day in plan for pid in day['places']]
                        self.assertEqual(len(ids), len(set(ids)))
                        self.assertEqual(len(plan), days)
                        for day in plan:
                            self.assertLessEqual(len(day['places']), 1 if pace == 'tranquilo' else 2)
                            places = [get_place(pid) for pid in day['places']]
                            self.assertLessEqual(len({p['region'] for p in places}), 1)
                            for p in places:
                                self.assertEqual(p['city'], city)
                                self.assertTrue(interest == 'misto' or p['interest'] == interest)
                        state = dict(city=city, days=days, interest=interest, pace=pace, plan=plan)
                        self.assertLessEqual(len(render(state)), 1024)
                        self.assertLessEqual(len(sources(state)), 4096)

    def test_known_closures_and_calendar_rollover(self):
        plan = build_plan('sao_paulo', 3, 'cultura', 'equilibrado', date(2026, 9, 28))
        self.assertNotIn('masp', plan[0]['places'])  # Monday.
        self.assertNotIn('pina', plan[1]['places'])  # Tuesday.
        plan = build_plan('sao_paulo', 3, 'cultura', 'equilibrado', date(2026, 12, 31))
        self.assertEqual(plan[1]['date'], '2027-01-01')
        self.assertNotIn('masp', plan[0]['places'] + plan[1]['places'])

    def test_exclusions_and_sparse_catalog_are_honest(self):
        plan = build_plan('bogota', 3, 'cultura', 'equilibrado', excluded=('botero', 'oro'))
        self.assertTrue(all(not day['places'] for day in plan))
        text = render(dict(city='bogota', interest='cultura', pace='equilibrado', plan=plan))
        self.assertIn('não há outro local', text)
        self.assertNotIn('R$', text)

    def test_invalid_configuration_cannot_silently_expand_scope(self):
        for args in [('unknown', 1, 'misto', 'tranquilo'), ('bogota', 4, 'misto', 'tranquilo'),
                     ('bogota', True, 'misto', 'tranquilo'), ('bogota', 1, 'food', 'tranquilo')]:
            with self.assertRaises(ValueError):
                build_plan(*args)


class ItineraryConversationTests(unittest.TestCase):
    def setUp(self):
        self.search = Mock(side_effect=AssertionError('Sightseeing must not query flight fares'))
        self.bot = Conversation(flight_search=self.search)
        self.today = date(2026, 9, 24)

    def send(self, text, user='a'):
        return self.bot.reply(user, text, today=self.today)

    def complete(self):
        for text in ('roteiro para São Paulo', 'sem data', '3 dias', 'misto', 'equilibrado', 'montar'):
            answer = self.send(text)
        return answer

    def test_end_to_end_preserves_flight_state_and_requires_confirmation(self):
        original = {'origin': 'CNF', 'destination': 'BOG', 'result': {'offers': []}}
        self.bot.sessions['a'] = Session('return', original.copy())
        self.send('roteiro')
        for text in ('Bogotá', 'dia 23 de outubro desse ano', 'dois dias', 'cultura', 'tranquilo'):
            answer = self.send(text)
        self.assertIn('Montar roteiro:', answer)
        self.assertNotIn('plan', self.bot.sessions['a'].values['_itinerary'])
        self.assertIn('23/10/2026', self.send('montar'))
        self.send('voltar aos voos')
        session = self.bot.sessions['a']
        self.assertEqual(session.step, 'return')
        for key, value in original.items():
            self.assertEqual(session.values[key], value)
        self.assertIn('Seu roteiro sugerido', self.send('meu roteiro'))

    def test_invalid_dates_days_and_preferences_do_not_advance(self):
        self.send('roteiro para Bogotá')
        self.assertIn('data futura', self.send('ontem'))
        self.assertEqual(self.bot.sessions['a'].values['_itinerary']['stage'], 'start')
        self.send('sem data')
        self.assertIn('1 a 3', self.send('30 dias'))
        self.send('1')
        self.assertIn('Outros interesses', self.send('gastronomia'))
        self.send('natureza')
        self.assertIn('Qual ritmo', self.send('correndo'))

    def test_greeting_repeats_current_prompt_without_changing_itinerary(self):
        self.send('roteiro para Bogotá')
        state = self.bot.sessions['a'].values['_itinerary']
        before = json.loads(json.dumps(state))
        answer = self.send('boa tarde')
        self.assertIn('primeiro dia', answer)
        self.assertEqual(state, before)
        self.search.assert_not_called()

    def test_unsupported_city_is_not_substituted(self):
        self.assertIn('Ainda não tenho', self.send('roteiro para Paris'))
        self.assertNotIn('city', self.bot.sessions['a'].values['_itinerary'])

    def test_edits_invalidate_generated_plan_and_require_new_confirmation(self):
        self.complete()
        self.send('ajustar roteiro')
        self.send('mudar ritmo')
        self.send('tranquilo')
        state = self.bot.sessions['a'].values['_itinerary']
        self.assertNotIn('plan', state)
        self.assertEqual(state['stage'], 'confirm')
        self.send('montar')
        self.assertTrue(all(len(d['places']) <= 1 for d in state['plan']))

    def test_removal_and_sources_only_reference_remaining_places(self):
        self.complete()
        self.send('remover passeio')
        self.send('remover masp')
        self.send('montar')
        self.assertNotIn('masp.com.br', self.send('fontes do roteiro'))
        self.assertNotIn('masp', [p for d in self.bot.sessions['a'].values['_itinerary']['plan'] for p in d['places']])

    def test_persists_through_json_reload_and_isolates_users(self):
        self.complete()
        session = self.bot.sessions['a']
        restored = Conversation(flight_search=self.search)
        restored.sessions['a'] = Session(session.step, json.loads(json.dumps(session.values)))
        self.assertIn('Seu roteiro sugerido', restored.reply('a', 'meu roteiro', today=self.today))
        self.assertIn('ainda não', restored.reply('b', 'meu roteiro', today=self.today))
        restored.reply('a', 'apagar roteiro', today=self.today)
        self.assertNotIn('_itinerary', restored.sessions['a'].values)

    def test_offline_demo_can_plan_without_paid_or_live_services(self):
        self.bot = Conversation()
        self.assertIn('Seu roteiro sugerido', self.complete())

    def test_native_choices_are_bounded_and_sources_remain_text(self):
        for text in ('roteiro', 'São Paulo', 'sem data', '3', 'misto', 'equilibrado', 'montar', 'ajustar roteiro'):
            answer = self.send(text)
            session = self.bot.sessions['a']
            payload = payload_for(session, answer)
            self.assertEqual(payload['interactive']['type'], 'list')
            rows = payload['interactive']['action']['sections'][0]['rows']
            self.assertLessEqual(len(rows), 10)
            self.assertTrue(all(len(r['title']) <= 24 for r in rows))
        previous = set(session.values['_choices'])
        answer = self.send('meu roteiro')
        payload_for(session, answer)
        self.assertTrue(previous.isdisjoint(session.values['_choices']))
        self.assertEqual(payload_for(session, self.send('fontes do roteiro'))['type'], 'text')

    def test_confirmation_after_midnight_rejects_past_start(self):
        for text in ('roteiro para Bogotá', 'hoje', '1', 'misto', 'tranquilo'):
            self.send(text)
        self.today = date(2026, 9, 25)
        self.assertIn('data inicial passou', self.send('montar'))

    def test_feature_menu_can_leave_itinerary_and_resume_pending_flight_question(self):
        self.bot.sessions['a'] = Session('adults', {'origin': 'CNF', 'destination': 'BOG'})
        self.complete()
        answer = self.send('o que você faz?')
        session = self.bot.sessions['a']
        payload = payload_for(session, answer)
        self.assertEqual(len(payload['interactive']['action']['sections'][0]['rows']), 6)
        self.assertFalse(session.values['_itinerary']['active'])
        self.assertIn('Quantos adultos', self.send('voos'))
        self.assertEqual(session.step, 'adults')
        self.assertIn('Seu roteiro sugerido', self.send('meu roteiro'))

    def test_leaving_itinerary_repeats_pending_flight_question(self):
        self.bot.sessions['a'] = Session('return', {'origin': 'CNF', 'destination': 'BOG'})
        self.complete()
        self.assertIn('data de volta', self.send('voltar aos voos'))

    def test_menu_marker_does_not_leak_into_following_response(self):
        self.send('menu')
        answer = self.send('roteiro')
        payload = payload_for(self.bot.sessions['a'], answer)
        self.assertEqual(payload['interactive']['action']['button'], 'Opções do roteiro')
