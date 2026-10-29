import tempfile
import unittest
from pathlib import Path

from app import make_server
from storage import Store


class BindTests(unittest.TestCase):
    def test_duplicate_start_cannot_rebind_or_interrupt_existing_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.db';server=make_server(path,0);store=Store(path)
            try:
                with store.db() as db:
                    db.execute("INSERT INTO submissions (id,problem_id,created,day,code,code_hash,mode,status,passed,total,completed,version,milliseconds,memory_kb) VALUES ('port-test',1,'x','x','x','x','submit','QUEUED',0,0,0,'test',0,0)")
                with self.assertRaises(OSError):make_server(path,server.server_port)
                with store.db() as db:
                    self.assertEqual(db.execute("SELECT status FROM submissions WHERE id='port-test'").fetchone()[0],'QUEUED')
            finally:server.server_close()


if __name__=='__main__':unittest.main()
