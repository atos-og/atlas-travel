import unittest
from datetime import date

from atlas.nlu_audit import CASES, evaluate


class NluAuditTests(unittest.TestCase):
    def test_evaluation_uses_only_synthetic_cases_and_counts_results(self):
        expected = {label: answer for label, _, _, _, answer in CASES}
        calls = []

        def interpreter(phrase, step, today, values, config):
            label = CASES[len(calls)][0]
            calls.append((phrase, step, today, values, config))
            return expected[label]

        result = evaluate({'GROQ_API_KEY': 'never-returned'}, interpreter=interpreter,
                          today=date(2026, 9, 28))
        self.assertTrue(result['ok'])
        self.assertEqual(result['passed'], len(CASES))
        self.assertEqual(len(calls), len(CASES))
        self.assertNotIn('never-returned', str(result))

    def test_failure_identifies_case_without_hiding_it(self):
        result = evaluate({}, interpreter=lambda *args: 'unexpected')
        self.assertFalse(result['ok'])
        self.assertEqual(result['passed'], 0)
        self.assertEqual(result['checks'][0]['case'], 'capabilities')

    def test_can_run_a_small_subset_within_free_tier_limits(self):
        subset = tuple(case for case in CASES if case[0] in {'bus', 'alerts'})
        expected = iter(('duvida onibus', 'duvida alertas'))
        result = evaluate({}, cases=subset, interpreter=lambda *args: next(expected))
        self.assertTrue(result['ok'])
        self.assertEqual(result['total'], 2)


if __name__ == '__main__':
    unittest.main()
