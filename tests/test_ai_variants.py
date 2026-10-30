import json
import random
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

from ai_settings import AISettings
from ai_variants import AIError,GATE,MAX_RESPONSE,TITLES,call_chat,generate_variant,parse_json,validate_candidate
from judge.cases import random_case
from variants import fixed_bundle


def candidate():
    return dict(title='复核两笔候选收支',statement='某结算台按原始录入顺序保存整数收支记录。现在给定一个合计金额，需要定位唯一两条不同记录，使其金额之和等于合计；金额可以为负，报告位置而不是金额。',
                condition_ids=[1,2],examples=[[[4,6,9],10],[[8,-3,2],5]])


class FakeHandler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get('Content-Length','0')))
        self.server.received.append(dict(path=self.path,body=json.loads(body),authorization=self.headers.get('Authorization')))
        status,raw,headers,delay=self.server.responses.pop(0)
        if delay:time.sleep(delay)
        try:
            self.send_response(status)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
            for name,value in headers.items():self.send_header(name,value)
            self.end_headers();self.wfile.write(raw)
        except OSError:pass


class AIVariantTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.settings=AISettings(Path(self.tmp.name)/'test.ai-settings.json')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),FakeHandler)
        self.server.received=[];self.server.responses=[]
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stop)
        self.base=f'http://127.0.0.1:{self.server.server_port}/v1'
        self.settings.save(dict(base_url=self.base,model='fake-model',api_key='fake-local-test-key'))

    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def enqueue(self,content,finish='stop'):
        raw=json.dumps(dict(choices=[dict(finish_reason=finish,message=dict(content=json.dumps(content,ensure_ascii=False)))]),ensure_ascii=False).encode()
        self.server.responses.append((200,raw,{},0))

    def test_real_local_http_generation_and_review(self):
        self.enqueue(candidate());self.enqueue(dict(equivalent=True,issues=[]))
        result=generate_variant(1,self.settings)
        self.assertEqual(result['sample_output'],'0 1\n0 1\n')
        self.assertEqual(result['model'],'fake-model');self.assertEqual(len(self.server.received),2)
        for call in self.server.received:
            self.assertEqual(call['path'],'/v1/chat/completions')
            self.assertEqual(call['authorization'],'Bearer fake-local-test-key')
            self.assertEqual(set(call['body']),{'model','messages','stream'})
            self.assertFalse(call['body']['stream'])
            payload=json.loads(call['body']['messages'][1]['content'])
            self.assertNotIn('draft',payload);self.assertNotIn('notes',payload);self.assertNotIn('code',payload)
        self.assertNotIn('fake-local-test-key',json.dumps(result))

    def test_semantic_review_rejection_does_not_echo_provider_content(self):
        self.enqueue(candidate());self.enqueue(dict(equivalent=False,issues=['provider-private-diagnostic: 原条件被修改']))
        with self.assertRaises(AIError) as error:generate_variant(1,self.settings)
        self.assertNotIn('fake-local-test-key',str(error.exception))
        self.assertNotIn('provider-private-diagnostic',str(error.exception))
        self.assertIn('一致性',str(error.exception))

    def test_missing_conditions_and_invalid_input_rejected(self):
        for change in ('conditions','input','extra','hint','identity','repeat'):
            value=candidate()
            if change=='conditions':value['condition_ids']=[1]
            if change=='input':value['examples'][0]=[[1,2],99]
            if change=='extra':value['constraints']='rewrite constraints'
            if change=='hint':value['statement']+='可以使用哈希表求出结果。'
            if change=='identity':value['title']='两数之和新场景'
            if change=='repeat':value['statement']=fixed_bundle(1)['versions'][0]['statement']
            with self.subTest(change=change),self.assertRaises(AIError):validate_candidate(1,fixed_bundle(1),value)

    def test_exponential_example_sizes_are_rejected_before_oracle(self):
        for number,examples in [(207,[[2000,[]],[1,[]]]),(31,[[list(range(8))],[[1,0]]]),(1143,[['a'*13,'a'],['a','b']])]:
            bundle=fixed_bundle(number);value=candidate()
            value['condition_ids']=list(range(1,len(bundle['conditions'])+1));value['examples']=examples
            with self.subTest(number=number),self.assertRaises(AIError):validate_candidate(number,bundle,value)

    def test_malformed_json_wrong_shape_and_truncated_reply(self):
        for raw in (b'not json fake-local-test-key',b'{}',b'{"choices":[]}'):
            self.server.responses.append((200,raw,{},0))
            with self.subTest(raw=raw),self.assertRaises(AIError) as error:call_chat(self.settings,[])
            self.assertNotIn('fake-local-test-key',str(error.exception))
        self.enqueue(candidate(),finish='length')
        with self.assertRaises(AIError):call_chat(self.settings,[])

    def test_http_errors_and_redirect_do_not_leak_or_forward_key(self):
        for status in (401,429,500,302):
            headers={'Location':self.base+'/redirect-target'} if status==302 else {}
            self.server.responses.append((status,b'fake-local-test-key reflected',headers,0))
            count=len(self.server.received)
            with self.subTest(status=status),self.assertRaises(AIError) as error:call_chat(self.settings,[])
            self.assertNotIn('fake-local-test-key',str(error.exception))
            self.assertEqual(len(self.server.received),count+1)

    def test_timeout_and_oversized_reply(self):
        self.server.responses.append((200,b'{}',{},.2))
        with self.assertRaises(AIError) as error:call_chat(self.settings,[],timeout=.03)
        self.assertIn('超时',str(error.exception))
        self.server.responses.append((200,b'x'*(MAX_RESPONSE+1),{},0))
        with self.assertRaises(AIError) as error:call_chat(self.settings,[])
        self.assertIn('过大',str(error.exception))

    def test_json_fences_are_data_and_nonfinite_rejected(self):
        self.assertEqual(parse_json('```json\n{"ok": true}\n```'),{'ok':True})
        for value in ('[]','{"x":NaN}','not a JSON object'):
            with self.subTest(value=value),self.assertRaises(AIError):parse_json(value)

    def test_busy_generation_has_no_second_request(self):
        GATE.acquire()
        try:
            with self.assertRaises(AIError):generate_variant(1,self.settings)
            self.assertEqual(self.server.received,[])
        finally:GATE.release()

    def test_provider_echoed_key_in_valid_content_is_not_displayed(self):
        value=candidate();value['statement']+='fake-local-test-key';self.enqueue(value)
        with self.assertRaises(AIError) as error:call_chat(self.settings,[])
        self.assertNotIn('fake-local-test-key',str(error.exception))

    def test_invalid_candidate_does_not_spend_review_request(self):
        value=candidate();value['condition_ids']=[];self.enqueue(value)
        with self.assertRaises(AIError):generate_variant(1,self.settings)
        self.assertEqual(len(self.server.received),1)

    def test_unique_shortest_window_guarantee_preserved_in_ai_examples(self):
        value=candidate();value['examples']=[['abxba','ab'],['a','a']]
        with self.assertRaises(AIError) as error:validate_candidate(76,fixed_bundle(76),value)
        self.assertIn('唯一',str(error.exception))

    def test_configuration_is_frozen_for_both_requests(self):
        self.enqueue(candidate());self.enqueue(dict(equivalent=True,issues=[]))
        def transport(snapshot,messages,timeout):
            result=call_chat(snapshot,messages,timeout)
            if len(self.server.received)==1:
                self.settings.save(dict(base_url=self.base+'/changed',model='changed-model',api_key='fake-changed-key'))
            return result
        result=generate_variant(1,self.settings,transport=transport)
        self.assertEqual(result['model'],'fake-model')
        self.assertEqual([call['path'] for call in self.server.received],['/v1/chat/completions']*2)
        self.assertEqual([call['authorization'] for call in self.server.received],['Bearer fake-local-test-key']*2)

    def test_sample_decoder_and_independent_verifier_cover_all_100(self):
        # This tests only structured example validation, not natural language
        # equivalence; the fixture narrative is never passed to model review.
        for number in TITLES:
            rng=random.Random(202610301000+number);bundle=fixed_bundle(number)
            for attempt in range(200):
                value=candidate();value['title']=f'本地示例校验场景 {number}'
                value['condition_ids']=list(range(1,len(bundle['conditions'])+1))
                value['examples']=[random_case(number,rng),random_case(number,rng)]
                try:result=validate_candidate(number,bundle,value)
                except AIError:continue
                self.assertTrue(result['sample_input']);break
            else:self.fail(f'No small valid example fixture found for {number}')
