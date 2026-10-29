import random
import unittest

from catalog import catalogue
from judge.cases import EDGES, random_case
from judge.mutations import LABELS, faulty
from judge.protocols import encode_answer, judge_output
from judge.reference import solve


class MutationTests(unittest.TestCase):
    def test_every_problem_rejects_named_common_error(self):
        self.assertEqual(set(LABELS),{p['number'] for p in catalogue()})
        for n,label in LABELS.items():
            with self.subTest(number=n,error=label):
                rng=random.Random(2026102900+n)
                cases=EDGES[n]+[random_case(n,rng) for _ in range(32)]
                detected=False
                for args in cases:
                    output=encode_answer(n,faulty(n,args))
                    if not judge_output(n,[args],[solve(n,args)],output)[0]['ok']:
                        detected=True;break
                self.assertTrue(detected,f'No counterexample for {n}: {label}')


if __name__=='__main__':unittest.main()
