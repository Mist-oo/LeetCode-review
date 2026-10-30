import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

import ai_cache
from ai_settings import AISettings
from ai_cache import AIReviewCache
from ai_variants import AIError,PROMPT_VERSION,validate_candidate
from storage import Store


class AICacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name)/'test.db');self.settings=AISettings(Path(self.tmp.name)/'test.ai-settings.json')
        self.settings.save(dict(base_url='https://example.invalid/v1',model='fake-model',api_key='fake-local-test-key'))
        self.calls=0;self.fail=False;self.cache=AIReviewCache(self.store,self.settings,self.generator)

    def generator(self,number,settings,previous=None):
        self.calls+=1
        if self.fail:raise AIError('模拟生成失败')
        bundle=ai_cache.fixed_bundle(number)
        candidate=dict(title=f'缓存验收场景 {self.calls}',statement=f'本批次 {self.calls} 的整数收支记录按原顺序排列，需要找出唯一的两个不同位置，记录金额可以为负，其合计必须等于目标，返回两处位置。',
                       condition_ids=list(range(1,len(bundle['conditions'])+1)),examples=[[[4,6,9],10],[[8,-3,2],5]])
        result=validate_candidate(number,bundle,candidate,previous)
        result.update(created=datetime.now(timezone.utc).isoformat(),model=settings.public()['model'],
                      contract_version=bundle['content_version'],prompt_version=PROMPT_VERSION,review_passed=True,validation='本地模拟审核')
        return result

    def test_cache_persists_and_reuses_without_generation(self):
        first=self.cache.get_or_generate(1);second=self.cache.get_or_generate(1)
        self.assertFalse(first['cached']);self.assertTrue(second['cached']);self.assertEqual(self.calls,1)
        self.assertEqual(first['id'],second['id'])
        reopened=AIReviewCache(self.store,self.settings,self.generator)
        self.assertEqual(reopened.get_or_generate(1)['id'],first['id']);self.assertEqual(self.calls,1)

    def test_force_keeps_both_versions_and_returns_new(self):
        first=self.cache.get_or_generate(1);second=self.cache.get_or_generate(1,True)
        self.assertNotEqual(first['id'],second['id']);self.assertEqual(self.calls,2)
        self.assertEqual(self.cache.get_or_generate(1)['id'],second['id'])
        with self.store.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM ai_review_variants').fetchone()[0],2)

    def test_failed_replacement_preserves_previous(self):
        first=self.cache.get_or_generate(1);self.fail=True
        with self.assertRaises(AIError):self.cache.get_or_generate(1,True)
        self.assertEqual(self.cache.get_or_generate(1)['id'],first['id'])

    def test_model_or_contract_change_invalidates_cache(self):
        first=self.cache.get_or_generate(1)
        self.settings.save(dict(base_url='https://example.invalid/v1',model='other-model'))
        second=self.cache.get_or_generate(1);self.assertNotEqual(first['id'],second['id'])
        changed=ai_cache.fixed_bundle(1);changed['content_version']='changed-contract'
        with patch('ai_cache.fixed_bundle',return_value=changed):
            third=self.cache.get_or_generate(1);self.assertNotEqual(second['id'],third['id'])

    def test_rotated_key_reuses_cache_but_missing_config_does_not(self):
        first=self.cache.get_or_generate(1)
        self.settings.save(dict(base_url='https://example.invalid/v1',model='fake-model',api_key='fake-rotated-key'))
        self.assertEqual(self.cache.get_or_generate(1)['id'],first['id']);self.assertEqual(self.calls,1)
        self.settings.save(dict(base_url='',model='',clear_key=True))
        with self.assertRaises(AIError):self.cache.get_or_generate(1)

    def test_corrupted_cached_content_is_not_served(self):
        first=self.cache.get_or_generate(1)
        with self.store.db() as db:db.execute('UPDATE ai_review_variants SET variant_json=?',(json.dumps(dict(first,sample_output='wrong')) ,))
        new=self.cache.get_or_generate(1);self.assertNotEqual(first['id'],new['id']);self.assertEqual(self.calls,2)

    def test_no_secrets_or_daily_results_in_cache(self):
        self.cache.get_or_generate(1)
        with self.store.db() as db:
            raw=db.execute('SELECT variant_json FROM ai_review_variants').fetchone()[0]
            self.assertNotIn('fake-local-test-key',raw)
            self.assertEqual(db.execute('SELECT count(*) FROM records').fetchone()[0],0)

    def test_busy_cache_cannot_spend_a_second_generation(self):
        self.cache.lock.acquire()
        try:
            with self.assertRaises(AIError):self.cache.get_or_generate(1)
            self.assertEqual(self.calls,0)
        finally:self.cache.lock.release()

    def test_invalid_force_and_malformed_cache_fields(self):
        with self.assertRaises(ValueError):self.cache.get_or_generate(1,force='false')
        self.assertEqual(self.calls,0)
        first=self.cache.get_or_generate(1)
        with self.store.db() as db:db.execute('UPDATE ai_review_variants SET variant_json=?',(json.dumps(dict(first,sample_input=None)),))
        result=self.cache.get_or_generate(1)
        self.assertNotEqual(first['id'],result['id']);self.assertEqual(self.calls,2)
