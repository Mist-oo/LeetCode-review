import unittest
from completion import complete


class CompletionTests(unittest.TestCase):
    def test_local_variable_and_method(self):
        source='values = []\nvalues.ap'
        result=complete(dict(code=source,line=2,column=len('values.ap')))
        self.assertIn('append',[v['name'] for v in result['items']],result)

    def test_import_and_function_parameters(self):
        result=complete(dict(code='import collections\ncollections.de',line=2,column=len('collections.de')))
        self.assertIn('deque',[v['name'] for v in result['items']],result)
        result=complete(dict(code='def add(x, y):\n    return x + y\nadd(',line=3,column=4))
        self.assertTrue(result['signatures'],result)
        self.assertIn('x',result['signatures'][0]['text'])

    def test_source_is_not_executed(self):
        result=complete(dict(code='raise SystemExit(100)\nitems=[]\nitems.ap',line=3,column=8))
        self.assertIn('append',[v['name'] for v in result['items']],result)

    def test_variable_names_and_importable_modules(self):
        result=complete(dict(code='sample_values=[]\nsample_va',line=2,column=9))
        self.assertIn('sample_values',[v['name'] for v in result['items']],result)
        result=complete(dict(code='import collect',line=1,column=14))
        self.assertIn('collections',[v['name'] for v in result['items']],result)


if __name__=='__main__':unittest.main()
