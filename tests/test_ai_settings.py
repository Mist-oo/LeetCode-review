import json
import tempfile
import unittest
from pathlib import Path

from ai_settings import AISettings,service_url
from storage import ValidationError


class AISettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'test.ai-settings.json';self.settings=AISettings(self.path)

    def save(self,**changes):
        data=dict(base_url='https://example.invalid/v1/',model='test-model',api_key='fake-local-test-key');data.update(changes)
        return self.settings.save(data)

    def test_public_settings_never_reveal_key(self):
        self.assertFalse(self.settings.public()['configured']);result=self.save()
        self.assertTrue(result['configured']);self.assertNotIn('api_key',result)
        self.assertNotIn('fake-local-test-key',json.dumps(result))
        self.assertEqual(AISettings(self.path).credentials()['api_key'],'fake-local-test-key')
        self.assertEqual(self.settings.endpoint(),'https://example.invalid/v1/chat/completions')

    def test_blank_retains_key_and_explicit_clear_removes_it(self):
        self.save();self.settings.save(dict(base_url='https://example.invalid/v1',model='changed',api_key=''))
        self.assertTrue(self.settings.public()['has_key'])
        self.settings.save(dict(base_url='',model='',clear_key=True))
        self.assertFalse(self.settings.public()['has_key'])
        with self.assertRaises(ValidationError):self.settings.endpoint()

    def test_addresses_and_full_endpoint(self):
        for invalid in ('http://example.invalid/v1','https://user:pass@example.invalid','https://example.invalid?a=b','https://example.invalid/#x','file:///tmp/test','https://example.invalid:99999','https://example.invalid/ bad'):
            with self.subTest(url=invalid),self.assertRaises(ValidationError):service_url(invalid)
        self.assertEqual(service_url('http://127.0.0.1:9999/v1/'),'http://127.0.0.1:9999/v1')
        self.settings.save(dict(base_url='https://example.invalid/chat/completions',model='test',api_key='fake'))
        self.assertEqual(self.settings.endpoint(),'https://example.invalid/chat/completions')

    def test_bad_header_characters_rejected_before_write(self):
        with self.assertRaises(ValidationError):self.save(api_key='bad\r\nheader')
        self.assertFalse(self.path.exists())

    def test_corrupt_settings_have_safe_error_and_can_be_replaced(self):
        self.path.write_text('fake-local-test-key broken json','utf-8')
        with self.assertRaises(ValidationError) as error:self.settings.public()
        self.assertNotIn('fake-local-test-key',str(error.exception))
        self.save();self.assertTrue(self.settings.public()['configured'])
