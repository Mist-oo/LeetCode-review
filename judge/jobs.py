"""One active execution per local app; asynchronous progress and durable submits."""
import hashlib
import json
import queue
import random
import threading
import time
import uuid
from datetime import datetime,timezone
from functools import lru_cache

from .cases import suite
from .protocols import VERSION,decode_cases,encode_case,encode_answer,judge_output,public_spec
from .reference import solve
from .runner import execute
from .validation import validate
from storage import ValidationError,text,today

TERMINAL={'AC','WA','CE','RE','TLE','MLE','OLE','CANCELLED','IE','INTERRUPTED','DONE'}


@lru_cache(maxsize=4)
def prepared(number):
    return prepare(number)


def prepare(number,seed=None):
    cases=suite(number,seed,256 if seed is not None else 128)
    answers=[]
    for case in cases:
        validate(number,case['args']);answers.append(solve(number,case['args']))
    digest=hashlib.sha256(json.dumps([VERSION,number,cases,answers],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()[:16]
    return cases,answers,f'{VERSION}:{digest}'


def specification(number):
    meta=public_spec(number)
    cases=suite(number,random_count=0)[:2]
    meta['sample_input']=''.join(encode_case(number,c['args']) for c in cases)
    meta['sample_output']=''.join(encode_answer(number,solve(number,c['args'])) for c in cases)
    return meta


class Jobs:
    def __init__(self,store):
        self.store=store;self.lock=threading.RLock();self.jobs={};self.events={};self.closed=False
        self.queue=queue.Queue(maxsize=8)
        with store.db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,problem_id INTEGER NOT NULL REFERENCES problems(id),
                created TEXT NOT NULL,day TEXT NOT NULL,code TEXT NOT NULL,code_hash TEXT NOT NULL,
                mode TEXT NOT NULL,status TEXT NOT NULL,passed INTEGER NOT NULL,total INTEGER NOT NULL,
                completed INTEGER NOT NULL,version TEXT NOT NULL,seed INTEGER,
                milliseconds INTEGER NOT NULL,memory_kb INTEGER NOT NULL,
                detail TEXT NOT NULL DEFAULT '{}',revealed INTEGER NOT NULL DEFAULT 0
            )''')
            db.execute("UPDATE submissions SET status='INTERRUPTED' WHERE status IN ('QUEUED','RUNNING')")
        self.worker=threading.Thread(target=self.loop,daemon=True);self.worker.start()

    def create(self,pid,data,mode='submit'):
        p=self.store.problem(pid);code=text(data,'code',200000,True)
        if mode not in ('submit','strengthen','run'):
            raise ValidationError('未知运行模式')
        seed=data.get('seed')
        if seed is not None and (mode!='strengthen' or type(seed) is not int or not 0<=seed<2**31):
            raise ValidationError('随机种子应为 0 到 2147483647 的整数，且只用于随机加强')
        stdin=text(data,'stdin',8000000) if mode=='run' else ''
        if mode=='run':
            cases=decode_cases(p['number'],stdin)
            if len(cases)>32:raise ValidationError('自定义运行最多 32 组；完整批量检验请使用正式提交')
            for args in cases:validate(p['number'],args)
        with self.lock:
            if self.closed:raise ValidationError('判题服务已关闭')
            if self.queue.full():raise ValidationError('队列已满，请等待当前提交完成')
            # Keep completed transient runs bounded; formal history stays in DB.
            finished=[k for k,j in self.jobs.items() if j['status'] in TERMINAL]
            for key in finished[:-5]:self.jobs.pop(key,None);self.events.pop(key,None)
            identifier=uuid.uuid4().hex
            job=dict(id=identifier,problem_id=pid,number=p['number'],created=datetime.now(timezone.utc).isoformat(),
                     day=today(),code=code,code_hash=hashlib.sha256(code.encode()).hexdigest(),mode=mode,
                     status='QUEUED',passed=0,total=0,completed=0,version=VERSION,
                     seed=(seed if seed is not None else random.SystemRandom().randrange(2**31)) if mode=='strengthen' else None,
                     milliseconds=0,memory_kb=0,detail={},revealed=False,stdin=stdin)
            self.jobs[identifier]=job;self.events[identifier]=threading.Event()
            self.persist(job)
            self.queue.put_nowait(identifier)
            return self.public(job)

    def persist(self,job):
        if job['mode']=='run':return
        columns=('id','problem_id','created','day','code','code_hash','mode','status','passed','total','completed','version','seed','milliseconds','memory_kb','detail','revealed')
        values=[json.dumps(job[k],ensure_ascii=False) if k=='detail' else int(job[k]) if k=='revealed' else job[k] for k in columns]
        with self.store.db() as db:
            db.execute(f'INSERT OR REPLACE INTO submissions ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',values)

    def update(self,job,**values):
        with self.lock:
            job.update(values);self.persist(job)

    @staticmethod
    def public(job,include_code=False):
        result={k:v for k,v in job.items() if k not in ('code','stdin','detail')}
        if include_code:result['code']=job['code']
        if job['mode']=='run' or job.get('revealed'):
            result['detail']=job['detail']
        elif job['status']=='CE':
            result['message']=job['detail'].get('message','语法错误')
        elif job['status']=='IE':
            result['message']=job['detail'].get('message','本地判题服务发生错误，请重试')
        return result

    def get_job(self,identifier):
        with self.lock:
            if identifier in self.jobs:return self.jobs[identifier]
            with self.store.db() as db:
                row=db.execute('SELECT * FROM submissions WHERE id=?',(identifier,)).fetchone()
            if not row:raise LookupError('提交不存在')
            job=dict(row);job['detail']=json.loads(job['detail']);job['revealed']=bool(job['revealed'])
            return job

    def get(self,identifier):
        return self.public(self.get_job(identifier),include_code=True)

    def history(self,pid):
        self.store.problem(pid)
        with self.store.db() as db:
            rows=db.execute('SELECT * FROM submissions WHERE problem_id=? ORDER BY created DESC',(pid,)).fetchall()
        result=[]
        for row in rows:
            job=dict(row);job['detail']={}
            summary=self.public(job,include_code=False);summary.pop('detail',None)
            result.append(summary)
        return result

    def reveal(self,identifier):
        with self.lock:
            job=self.get_job(identifier)
            if job['status'] not in TERMINAL:raise ValidationError('请等待本次判题结束')
            job['revealed']=True;self.persist(job)
            return self.public(job,include_code=True)

    def cancel(self,identifier):
        with self.lock:
            job=self.get_job(identifier)
            if job['status'] not in TERMINAL:
                self.events[identifier].set()
            return self.public(job)

    def loop(self):
        while True:
            identifier=self.queue.get()
            if identifier is None:self.queue.task_done();break
            job=self.jobs[identifier]
            try:self.process(job,self.events[identifier])
            except Exception as error:
                # Do not turn a broken reference/checker into a student's WA.
                self.update(job,status='IE',detail={'message':f'判题内部错误：{type(error).__name__}: {error}'})
            finally:self.queue.task_done()

    def process(self,job,cancel):
        if cancel.is_set():self.update(job,status='CANCELLED');return
        self.update(job,status='RUNNING')
        if job['mode']=='run':
            args=decode_cases(job['number'],job['stdin'])
            expected=[solve(job['number'],a) for a in args]
            result=execute(job['code'],job['stdin'],cancel=cancel)
            checked=judge_output(job['number'],args,expected,result['stdout'])
            self.update(job,status='DONE' if result['status']=='OK' else result['status'],
                        total=len(args),completed=len(args),passed=sum(r['ok'] for r in checked),
                        milliseconds=result['milliseconds'],memory_kb=result['memory_kb'],
                        detail=dict(stdout=result['stdout'],stderr=result['stderr'],
                                    expected=''.join(encode_answer(job['number'],a) for a in expected),results=checked))
            return
        cases,answers,version=prepared(job['number']) if job['seed'] is None else prepare(job['number'],job['seed'])
        self.update(job,total=len(cases),version=version)
        normal=[i for i,c in enumerate(cases) if c['kind']!='pressure']
        batches=[normal[i:i+16] for i in range(0,len(normal),16)]+[[i] for i,c in enumerate(cases) if c['kind']=='pressure']
        final_status='AC';failure=None;passed=completed=elapsed=peak=0
        for batch in batches:
            if cancel.is_set():self.update(job,status='CANCELLED');return
            args=[cases[i]['args'] for i in batch];expected=[answers[i] for i in batch]
            stdin=''.join(encode_case(job['number'],a) for a in args)
            result=execute(job['code'],stdin,cancel=cancel)
            elapsed+=result['milliseconds'];peak=max(peak,result['memory_kb'])
            if result['status']=='CANCELLED':self.update(job,status='CANCELLED',milliseconds=elapsed,memory_kb=peak);return
            checked=judge_output(job['number'],args,expected,result['stdout'])
            if result['status']=='CE':
                self.update(job,status='CE',completed=0,milliseconds=elapsed,detail={'message':result['stderr']});return
            if result['status']=='IE':raise RuntimeError(result['stderr'])
            if result['status']!='OK':
                # A process timeout/error invalidates this batch's completion;
                # parsed prefix results can still be credited if fully framed.
                status=result['status']
                if all(r['ok'] for r in checked):checked[-1].update(ok=False,error='输出后程序未正常结束')
            else:status='AC' if all(r['ok'] for r in checked) else 'WA'
            passed+=sum(r['ok'] for r in checked)
            completed+=len(batch)
            if status!='AC' and failure is None:
                bad=next((i for i,r in enumerate(checked) if not r['ok']),len(batch)-1)
                failure=dict(group=batch[bad]+1,label=cases[batch[bad]]['label'],status=status,
                             input=encode_case(job['number'],args[bad]),expected=encode_answer(job['number'],expected[bad]),
                             actual=checked[bad]['actual'],error=checked[bad]['error'],
                             batch_input=stdin,batch_expected=''.join(encode_answer(job['number'],a) for a in expected),
                             batch_stdout=result['stdout'],stderr=result['stderr'])
                final_status=status
            self.update(job,passed=passed,completed=completed,milliseconds=elapsed,memory_kb=peak)
        if cancel.is_set():final_status='CANCELLED'
        self.update(job,status=final_status,detail=failure or {})

    def close(self):
        with self.lock:
            self.closed=True
            for event in self.events.values():event.set()
        # Queue is bounded; worker consumes cancelled entries immediately.
        self.queue.put(None);self.worker.join(timeout=8)
