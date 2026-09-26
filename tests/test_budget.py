import unittest
from datetime import date
from atlas.budget import parse_budget, BUDGET_PROMPT
from atlas.flights import rank, format_results
from atlas.conversation import Conversation, Session
from atlas.interactive import payload_for


def offer(price, key):
    return {'price': price, 'duration': 120, 'stops': 0,
            'journeys': [{'departure': '23/10 10:00', 'arrival': '23/10 11:00',
                          'duration': 60, 'stops': 0, 'airlines': key}],
            'url': 'https://www.google.com/travel/flights?offer=' + key}


class BudgetTests(unittest.TestCase):
    def test_budget_prompt_is_scannable(self):
        self.assertIn('*Qual é o limite para as passagens?*\n\n', BUDGET_PROMPT)
        self.assertIn('• R$ 1.500\n• 2 mil\n• sem limite', BUDGET_PROMPT)

    def test_brl_formats_and_no_limit(self):
        for text in ['até R$ 1.500,50', '1500,50', '1500.50']:
            self.assertEqual(parse_budget(text), '1500.50')
        self.assertEqual(parse_budget('2 mil reais'), '2000.00')
        self.assertEqual(parse_budget('até 1,5 mil'), '1500.00')
        self.assertIsNone(parse_budget('sem limite'))

    def test_reject_ambiguous_per_person_negative_and_multiple_amounts(self):
        for text in ['500 por pessoa', '1000 ou 2000', '-50', '0', 'NaN', 'USD 500', '1.23.45', '1,555', 'mil']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_budget(text)

    def test_filters_before_ranking_and_respects_exact_cent_boundary(self):
        offers = [offer('100.00','a'), offer('100.01','b'), offer('90','c')]
        self.assertEqual([o['price'] for o in rank(offers,'4','100.00')], ['100.00','90'])
        self.assertEqual(len(rank(offers,'1',None)),3)

    def setUp(self):
        self.offers = [offer('683','a'),offer('1430','b')]
        self.values = {'origin':'CNF','destination':'GRU','departure':'23/10/2027',
                       'return':'30/10/2027','adults':'2','priority':'1',
                       'result':{'status':'success','offers':self.offers,'checked_at':'test'}}

    def test_no_offer_in_budget_does_not_expose_a_purchase_option(self):
        values = dict(self.values,budget='500')
        message = format_results(values['result'],values)
        self.assertIn('acima do limite',message)
        self.assertIn('*Nenhuma oferta dentro de R$ 500,00*\n\n', message)
        session = Session('complete',values)
        payload_for(session,message)
        self.assertFalse(any(v.startswith('link ') for v in session.values['_choices'].values()))
        bot=Conversation(lambda _: self.fail('Refinement must not search'))
        bot.sessions['u']=session
        self.assertNotIn('https',bot.reply('u','link 1'))

    def test_budget_refines_cached_results_and_keeps_total_for_all_adults(self):
        bot=Conversation(lambda _: self.fail('Refinement must not search'))
        bot.sessions['u']=Session('complete',dict(self.values))
        self.assertIn('todos os adultos',bot.reply('u','tá caro'))
        answer=bot.reply('u','até 1000')
        self.assertIn('consulta anterior',answer)
        self.assertEqual(bot.sessions['u'].values['budget'],'1000.00')
        self.assertNotIn('1.430,00',answer)
        self.assertIn(self.offers[0]['url'],bot.reply('u','link 1'))
        bot.reply('u','orçamento')
        bot.reply('u','sem limite')
        self.assertIn(self.offers[1]['url'],bot.reply('u','link 2'))

    def test_initial_budget_requires_confirmation_before_search(self):
        calls=[]
        def search(values):
            calls.append(values)
            return {'status':'empty','offers':[]}
        bot=Conversation(search)
        for text in ['oi','CNF','GRU','23/10/2027','30/10/2027','2','1','até 1500']:
            answer=bot.reply('u',text,today=date(2027,9,1))
        self.assertEqual(calls,[])
        self.assertIn('1.500,00',answer)
        self.assertIn('todos os adultos',answer)
        bot.reply('u','sim',today=date(2027,9,1))
        self.assertEqual(calls[0]['budget'],'1500.00')

    def test_menu_has_at_most_ten_rows_and_budget_skip_is_native(self):
        values=dict(self.values)
        values['result']={'status':'success','offers':[offer(str(i*100),str(i)) for i in range(1,5)]}
        session=Session('complete',values)
        payload=payload_for(session,'Ofertas')
        self.assertEqual(len(payload['interactive']['action']['sections'][0]['rows']),10)
        self.assertIn('orcamento',session.values['_choices'].values())
        session.step='budget'
        self.assertEqual(payload_for(session,'Informe o total')['interactive']['type'],'button')
