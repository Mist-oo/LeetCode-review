import copy
import json
import tempfile
import unittest
from pathlib import Path

from variants import fixed_bundle,validate_bundle,NUMBERS


def example_bundle():
    cases=[[[4,6,9],10],[[8,-3,2],5]]
    return dict(schema=1,number=1,conditions=['选择两个不同下标，和等于目标，恰好一个答案。'],
                constraints_html='<ul><li>2 &lt;= n &lt;= 10000</li></ul>',
                source='https://github.com/doocs/leetcode/blob/test/README.md',
                versions=[dict(id=f'fixed-1-{i}',title=f'场景 {i}',statement=f'在业务 {i} 中找出两笔合计恰好的记录。',
                               examples=copy.deepcopy(cases),expected_output='0 1\n0 1\n') for i in range(1,4)])


class VariantTests(unittest.TestCase):
    def test_bundle_contract_and_examples(self):
        self.assertEqual(validate_bundle(1,example_bundle())['number'],1)

    def test_duplicate_variants_rejected(self):
        bundle=example_bundle();bundle['versions'][1]['statement']=bundle['versions'][0]['statement']
        with self.assertRaises(ValueError):validate_bundle(1,bundle)

    def test_bad_examples_or_wrong_answer_rejected(self):
        for change in ('input','answer'):
            bundle=example_bundle()
            if change=='input':bundle['versions'][0]['examples'][0]=[[1,2],99]
            else:bundle['versions'][0]['expected_output']='0 2\n0 2\n'
            with self.subTest(change=change),self.assertRaises(ValueError):validate_bundle(1,bundle)

    def test_count_id_and_number_rejected(self):
        for change in ('count','id','number'):
            bundle=example_bundle()
            if change=='count':bundle['versions'].pop()
            elif change=='id':bundle['versions'][0]['id']='unstable'
            else:bundle['number']=49
            with self.subTest(change=change),self.assertRaises(ValueError):validate_bundle(1,bundle)

    def test_public_bundle_and_content_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'1.json';bundle=example_bundle();path.write_text(json.dumps(bundle),'utf-8')
            result=fixed_bundle(1,folder)
            self.assertTrue(result['available']);self.assertEqual(len(result['versions']),3)
            self.assertEqual(result['content_version'],fixed_bundle(1,folder)['content_version'])
            self.assertNotIn('examples',result['versions'][0])
            bundle['conditions'].append('任意合法顺序均可。');path.write_text(json.dumps(bundle),'utf-8')
            self.assertNotEqual(result['content_version'],fixed_bundle(1,folder)['content_version'])

    def test_missing_bundle_and_unknown_problem(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(fixed_bundle(1,folder)['available'])
            with self.assertRaises(LookupError):fixed_bundle(999999,folder)

    def test_every_available_bundled_statement(self):
        for number in sorted(NUMBERS):
            with self.subTest(number=number):
                bundle=fixed_bundle(number)
                if bundle['available']:self.assertEqual(len(bundle['versions']),3)
