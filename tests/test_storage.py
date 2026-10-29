import tempfile
import unittest
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

    def test_custom_problem_requires_leetcode_url_and_unique_number(self):
        data = dict(number=999999, title='测试', category='自定义', description='内容', url='https://leetcode.cn/problems/test/')
        pid = self.store.add_problem(data)
        self.assertEqual(self.store.problem(pid)['collection'], '自选题目')
        with self.assertRaises(ValidationError):
            self.store.add_problem(data)
        with self.assertRaises(ValidationError):
            self.store.add_problem(dict(data, number=888888, url='javascript:alert(1)'))


if __name__ == '__main__':
    unittest.main()
