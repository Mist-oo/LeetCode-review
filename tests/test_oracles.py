import unittest

from catalog import catalogue
from judge.cases import EDGES, random_case,endpoint_cases
from judge.oracle import oracle
from judge.protocols import accepts
from judge.reference import solve
from judge.validation import validate
import random


class OracleTests(unittest.TestCase):
    def test_all_100_against_independent_small_oracles(self):
        compared=0
        for p in catalogue():
            n=p['number'];rng=random.Random(88000+n)
            for index,args in enumerate(EDGES[n]+endpoint_cases(n)+[random_case(n,rng) for _ in range(32)]):
                with self.subTest(number=n,case=index):
                    validate(n,args)
                    expected=oracle(n,args)
                    actual=solve(n,args)
                    self.assertTrue(accepts(n,args,actual,expected),(n,args,actual,expected))
                    self.assertTrue(accepts(n,args,expected,actual),(n,args,actual,expected))
                    compared+=1
        print(f'Independent small-oracle comparison: 100 problems, {compared} groups')


if __name__=='__main__':
    unittest.main()
