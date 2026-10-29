import tempfile
import time
import unittest
from pathlib import Path

from storage import Store,today
from storage import ValidationError
from judge.jobs import Jobs,TERMINAL

TWO_SUM = '''import sys
lines=iter(sys.stdin.read().splitlines())
for line in lines:
    n=int(line)
    values=list(map(int,next(lines).split()))
    target=int(next(lines))
    seen={}
    for i,x in enumerate(values):
        if target-x in seen:
            print(seen[target-x],i)
            break
        seen[x]=i
'''


class JobTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(Path(self.tmp.name)/'test.db');self.jobs=Jobs(self.store)

    def tearDown(self):
        self.jobs.close();self.tmp.cleanup()

    def wait(self,identifier):
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            job=self.jobs.get(identifier)
            if job['status'] in TERMINAL:return job
            time.sleep(.02)
        self.fail('Local judge job did not finish')

    def test_ac_is_durable_and_daily_result_remains_manual(self):
        start=self.jobs.create(1,{'code':TWO_SUM});result=self.wait(start['id'])
        self.assertEqual(result['status'],'AC',result)
        self.assertEqual(result['passed'],result['total'])
        self.assertNotIn('detail',result)
        self.assertEqual(self.store.history(1),[])
        self.store.save_record(1,dict(day=today(),result='fail',code=TWO_SUM,tags=['看了提示']))
        record=self.store.history(1)[0]
        self.assertEqual(record['result'],'fail')
        self.assertEqual(record['judgment']['status'],'AC')
        self.store.save_record(1,dict(day=today(),result='pass',code=TWO_SUM+'\n# edited'))
        self.assertIsNone(self.store.history(1)[0]['judgment'])
        self.assertEqual(len(self.jobs.history(1)),1)

    def test_failed_case_hidden_until_reveal_and_reproducible(self):
        source='import sys\nsys.stdin.read()\nprint("0 0")'
        first=self.wait(self.jobs.create(1,{'code':source})['id'])
        self.assertEqual(first['status'],'WA')
        self.assertNotIn('detail',first)
        reveal=self.jobs.reveal(first['id'])
        self.assertIn('batch_input',reveal['detail'])
        second=self.wait(self.jobs.create(1,{'code':source})['id'])
        self.assertEqual(first['version'],second['version'])
        self.assertEqual(first['passed'],second['passed'])
        self.assertEqual(len(self.jobs.history(1)),2)

    def test_custom_run_does_not_enter_submission_history(self):
        result=self.wait(self.jobs.create(1,{'code':TWO_SUM,'stdin':'2\n2 7\n9\n2\n3 3\n6\n'},'run')['id'])
        self.assertEqual(result['status'],'DONE',result)
        self.assertEqual(result['passed'],2)
        self.assertEqual(self.jobs.history(1),[])

    def test_cancel_and_restart_history(self):
        result=self.jobs.create(1,{'code':'while True: pass'})
        self.jobs.cancel(result['id'])
        self.assertEqual(self.wait(result['id'])['status'],'CANCELLED')
        self.jobs.close();self.jobs=Jobs(self.store)
        self.assertEqual(self.jobs.get(result['id'])['status'],'CANCELLED')

    def test_runtime_failure_after_correct_output_is_not_ac(self):
        result=self.wait(self.jobs.create(1,{'code':TWO_SUM+'\nraise RuntimeError("after output")'})['id'])
        self.assertEqual(result['status'],'RE',result)
        self.assertLess(result['passed'],result['total'])

    def test_strengthening_seed_is_reproducible(self):
        data=dict(code=TWO_SUM,seed=712345)
        first=self.wait(self.jobs.create(1,data,'strengthen')['id'])
        second=self.wait(self.jobs.create(1,data,'strengthen')['id'])
        self.assertEqual(first['status'],'AC',first)
        self.assertEqual(first['version'],second['version'])
        self.assertEqual(first['seed'],712345)
        self.assertGreater(first['total'],200)

    def test_custom_run_rejects_unbounded_batch(self):
        with self.assertRaises(ValidationError):
            self.jobs.create(1,dict(code=TWO_SUM,stdin='2\n2 7\n9\n'*33),'run')


if __name__=='__main__':unittest.main()
