import threading
import time
import unittest

from judge.runner import execute


class RunnerTests(unittest.TestCase):
    def test_eof_multiple_cases_and_input(self):
        result=execute('import sys\nfor line in sys.stdin:\n print(sum(map(int,line.split())))\n','1 2\n3 4\n')
        self.assertEqual(result['status'],'OK',result)
        self.assertEqual(result['stdout'],'3\n7\n')

    def test_compile_runtime_and_timeout(self):
        self.assertEqual(execute('if :','')['status'],'CE')
        self.assertEqual(execute('raise ValueError("oops")','')['status'],'RE')
        result=execute('while True: pass','',seconds=.15)
        self.assertEqual(result['status'],'TLE',result)
        self.assertLess(result['milliseconds'],2500)

    def test_output_limit_and_cancel(self):
        self.assertEqual(execute('while True: print("x"*8192)','',output_bytes=32768)['status'],'OLE')
        cancel=threading.Event();timer=threading.Timer(.1,cancel.set);timer.start()
        result=execute('while True: pass','',cancel=cancel)
        timer.join();self.assertEqual(result['status'],'CANCELLED')

    def test_memory_monitor(self):
        result=execute('a=[]\nwhile True: a.append(bytearray(1024*1024))','',memory_mb=40)
        self.assertEqual(result['status'],'MLE',result)

    def test_child_is_removed_even_if_parent_exits(self):
        # The child holds inherited stdout. Without process-tree cleanup this
        # call would hang and leak a 60-second sleeper after the parent exits.
        result=execute('import subprocess,sys\nsubprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"])\nprint("done")','',seconds=2)
        self.assertEqual(result['status'],'OK',result)
        self.assertLess(result['milliseconds'],2500)


if __name__=='__main__':unittest.main()
