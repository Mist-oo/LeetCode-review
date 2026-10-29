import time
import unittest

from catalog import catalogue
from judge.cases import suite
from judge.protocols import (SPECS, ProtocolError, accepts, decode_cases,
                             encode_answer, encode_case, judge_output, public_spec)
from judge.reference import solve
from judge.validation import validate


class ProtocolTests(unittest.TestCase):
    def test_all_100_input_output_roundtrips(self):
        self.assertEqual(set(SPECS), {p['number'] for p in catalogue()})
        total = 0
        for p in catalogue():
            n = p['number']
            with self.subTest(number=n):
                cases = suite(n)
                args = [c['args'] for c in cases]
                for a in args:
                    validate(n,a)
                self.assertEqual(decode_cases(n, ''.join(encode_case(n, a) for a in args)), args)
                answers = [solve(n, a) for a in args]
                results = judge_output(n, args, answers, ''.join(encode_answer(n, a) for a in answers))
                self.assertTrue(all(r['ok'] for r in results), [(i,r) for i,r in enumerate(results) if not r['ok']][:1])
                self.assertTrue(public_spec(n)['output'])
                total += len(cases)
        print(f'Input/output roundtrip: 100 problems, {total} groups')

    def test_empty_values_are_not_eof_or_ignored(self):
        args = [[''], ['abc'], ['']]
        source = ''.join(encode_case(3, a) for a in args)
        self.assertEqual(decode_cases(3, source), args)
        self.assertEqual(decode_cases(128, '0\n\n2\n1 2\n'), [[[]], [[1,2]]])
        with self.assertRaises(ProtocolError):
            decode_cases(1, '2\n1 2\n')

    def test_alternative_answers_and_multisets(self):
        self.assertTrue(accepts(1, [[2,7],9], [1,0], [0,1]))
        self.assertFalse(accepts(1, [[3,3],6], [0,0], [0,1]))
        self.assertTrue(accepts(5, ['babad'], 'aba', 'bab'))
        self.assertFalse(accepts(5, ['babad'], 'baba', 'bab'))
        self.assertTrue(accepts(108, [[1,2]], [1,None,2], [2,1]))
        self.assertFalse(accepts(108, [[1,2,3]], [1,None,2,None,3], [2,1,3]))
        self.assertFalse(accepts(226, [[]], [None,1], []))
        self.assertTrue(accepts(49, [['','a','']], [['a'],['','']], [['',''],['a']]))
        self.assertFalse(accepts(49, [['','a','']], [['a'],['']], [['',''],['a']]))
        self.assertFalse(accepts(78, [[1]], [[],[1],[1]], [[],[1]]))

    def test_bad_output_and_floats(self):
        self.assertFalse(accepts(4, [[1],[2]], float('nan'), 1.5))
        self.assertTrue(accepts(4, [[1],[2]], 1.5000001, 1.5))
        self.assertFalse(judge_output(1, [[[2,7],9]], [[0,1]], '0 1\nextra\n')[0]['ok'])
        result = judge_output(22, [[1],[2]], [['()'],['(())','()()']], 'wrong\n')
        self.assertEqual(len(result),2)
        self.assertTrue(all(not r['ok'] for r in result))


if __name__ == '__main__':
    unittest.main()
