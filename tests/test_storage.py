import tempfile
import unittest
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from catalog import catalogue
from storage import Store, ValidationError, today


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'test.db'
        self.store = Store(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_seed_and_reopen_are_idempotent(self):
        self.assertEqual(len(catalogue()), 100)
        self.assertEqual(len({p['number'] for p in catalogue()}), 100)
        self.assertEqual(len(Store(self.path).state()['problems']), 100)

    def test_mark_done_does_not_create_history(self):
        self.store.mark_done({'ids': [1, 2]})
        state = Store(self.path).state()
        self.assertEqual(sum(p['done'] for p in state['problems']), 2)
        self.assertEqual(state['records'], [])

    def test_failed_batch_rolls_back(self):
        with self.assertRaises(LookupError):
            self.store.mark_done({'ids': [1, 999999]})
        self.assertFalse(self.store.problem(1)['done'])

    def test_draft_has_no_result_and_next_day_is_blank(self):
        self.store.save_draft(1, {'day': today(), 'code': 'print(42)'})
        self.assertEqual(self.store.problem(1)['draft'], 'print(42)')
        self.assertEqual(self.store.history(1), [])
        tomorrow = (date.fromisoformat(today()) + timedelta(days=1)).isoformat()
        with patch('storage.today', return_value=tomorrow):
            self.assertEqual(self.store.problem(1)['draft'], '')

    def test_record_replaces_today_preserves_history_and_clears_stale_errors(self):
        self.store.save_record(1, dict(day=today(), result='fail', code='x', tags=['边界遗漏'], note='空数组'))
        self.store.save_record(1, dict(day=today(), result='pass', code='fixed', tags=['边界遗漏'], note='old'))
        history = Store(self.path).history(1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['result'], 'pass')
        self.assertEqual(history[0]['tags'], [])
        self.assertEqual(history[0]['note'], '')
        self.assertEqual(self.store.problem(1)['draft'], 'fixed')
        self.assertTrue(self.store.problem(1)['done'])

    def test_no_backdating_or_invalid_result(self):
        for data in [dict(day='2000-01-01', result='pass'), dict(day=today(), result='other')]:
            with self.assertRaises(ValidationError):
                self.store.save_record(1, data)
        self.assertEqual(self.store.history(1), [])

    def test_notes_and_custom_tags_persist_without_creating_record(self):
        self.store.save_notes(1, {'idea': '**哈希**', 'reference_code': 'print(1)'})
        self.store.add_tag({'name': '负数处理'})
        reopened = Store(self.path)
        self.assertEqual(reopened.problem(1)['notes']['idea'], '**哈希**')
        self.assertIn('负数处理', reopened.state()['tags'])
        self.assertEqual(reopened.history(1), [])

    def test_retired_custom_data_is_hidden_but_preserved(self):
        with self.store.db() as db:
            cursor=db.execute("INSERT INTO problems (number,title,slug,url,category,collection) VALUES (999999,'旧自选','old','https://leetcode.cn/problems/old/','自定义','自选题目')")
            pid=cursor.lastrowid
            db.execute("INSERT INTO notes (problem_id,idea) VALUES (?, '重要旧笔记')",(pid,))
        self.assertEqual(len(Store(self.path).state()['problems']),100)
        with self.assertRaises(LookupError):self.store.problem(pid)
        with self.store.db() as db:
            self.assertEqual(db.execute('SELECT idea FROM notes WHERE problem_id=?',(pid,)).fetchone()[0],'重要旧笔记')

    def test_v1_seven_column_record_migrates_without_loss(self):
        path=Path(self.tmp.name)/'old.db'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE records (problem_id INTEGER,day TEXT,result TEXT,code TEXT,tags TEXT,note TEXT,updated TEXT,PRIMARY KEY(problem_id,day))')
            db.execute("INSERT INTO records VALUES (1,'2020-01-01','fail','print(7)','[]','旧错误','old')")
        db.close()
        migrated=Store(path)
        old=migrated.history(1)[0]
        self.assertEqual(old['code'],'print(7)')
        self.assertEqual(old['note'],'旧错误')
        self.assertIsNone(old['judgment'])


if __name__ == '__main__':
    unittest.main()
