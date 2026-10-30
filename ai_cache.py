"""Durable checked AI statements, scoped by contract and configured provider."""
import hashlib
import json
import threading

from ai_settings import SettingsSnapshot
from ai_variants import AIError,PROMPT_VERSION,generate_variant,validate_candidate
from judge.protocols import decode_cases,public_spec
from variants import fixed_bundle
from storage import ValidationError


class AIReviewCache:
    def __init__(self,store,settings,generator=None):
        self.store=store;self.settings=settings;self.generator=generator or generate_variant;self.lock=threading.Lock()
        with store.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS ai_review_variants (
                    id TEXT PRIMARY KEY,number INTEGER NOT NULL REFERENCES problems(number),
                    contract_key TEXT NOT NULL,provider_key TEXT NOT NULL,created TEXT NOT NULL,
                    variant_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ai_review_lookup ON ai_review_variants(number,contract_key,provider_key);
            ''')

    @staticmethod
    def keys(number,bundle,settings):
        contract=json.dumps([bundle['content_version'],PROMPT_VERSION,public_spec(number)],ensure_ascii=False,sort_keys=True)
        provider=json.dumps([settings.public()['base_url'],settings.public()['model']],ensure_ascii=False)
        return hashlib.sha256(contract.encode()).hexdigest(),hashlib.sha256(provider.encode()).hexdigest()

    def validate_saved(self,number,bundle,settings,value):
        try:
            if not isinstance(value,dict) or value.get('review_passed') is not True:return None
            strings=('id','title','statement','sample_input','sample_output','created','model','contract_version','prompt_version','validation')
            if not all(isinstance(value.get(key),str) and len(value[key])<=30000 for key in strings):return None
            value={key:value[key] for key in (*strings,'condition_ids','review_passed')}
            if value.get('contract_version')!=bundle['content_version'] or value.get('prompt_version')!=PROMPT_VERSION or value.get('model')!=settings.public()['model']:return None
            if not isinstance(value.get('id'),str) or not value['id'].startswith('ai-') or not isinstance(value.get('created'),str):return None
            candidate=dict(title=value['title'],statement=value['statement'],condition_ids=value['condition_ids'],examples=decode_cases(number,value['sample_input']))
            checked=validate_candidate(number,bundle,candidate)
            if checked['sample_output']!=value['sample_output']:return None
            return value
        except (AIError,ValueError,TypeError,KeyError,IndexError,RecursionError):return None

    def latest(self,number,bundle,settings,keys):
        with self.store.db() as db:
            row=db.execute('SELECT variant_json FROM ai_review_variants WHERE number=? AND contract_key=? AND provider_key=? ORDER BY rowid DESC LIMIT 1',(number,*keys)).fetchone()
        if not row:return None
        try:value=json.loads(row[0])
        except (ValueError,TypeError,RecursionError):return None
        return self.validate_saved(number,bundle,settings,value)

    def get_or_generate(self,number,force=False):
        if type(force) is not bool:raise ValidationError('换个说法选项格式不正确')
        settings=SettingsSnapshot(self.settings.credentials())
        if not settings.public()['configured']:raise AIError('请先配置 AI 服务地址、模型名和密钥')
        bundle=fixed_bundle(number)
        if not bundle['available']:raise AIError('缺少该题固定条件，暂不能生成 AI 改写')
        keys=self.keys(number,bundle,settings)
        previous=self.latest(number,bundle,settings,keys)
        if previous and not force:return dict(previous,cached=True)
        if not self.lock.acquire(blocking=False):raise AIError('已有 AI 题面正在生成，请稍后再试')
        try:
            if not force:
                previous=self.latest(number,bundle,settings,keys)
                if previous:return dict(previous,cached=True)
            generated=self.generator(number,settings,previous=previous)
            variant=self.validate_saved(number,bundle,settings,generated)
            if not variant:raise AIError('AI 新版本未通过保存前检查，请使用固定改写')
            # Commit only a successfully checked version. Failed replacement
            # must never destroy a previous usable statement.
            with self.store.db() as db:
                db.execute('INSERT INTO ai_review_variants(id,number,contract_key,provider_key,created,variant_json) VALUES (?,?,?,?,?,?)',
                           (variant['id'],number,*keys,variant['created'],json.dumps(variant,ensure_ascii=False)))
            return dict(variant,cached=False)
        finally:self.lock.release()
