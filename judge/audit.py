"""Reproducible all-100 quality gate; run `python -m judge.audit`.

Produces an auditable coverage report only after every gate succeeds. A report
is evidence for this specific suite and implementation, not official equivalence.
"""
import hashlib
import json
import random
import time
from pathlib import Path

from catalog import catalogue
from .cases import EDGES,random_case
from .jobs import prepare
from .mutations import LABELS,faulty
from .oracle import oracle
from .protocols import accepts,encode_case,encode_answer,decode_cases,judge_output,SPECS
from .runner import execute
from .validation import validate

ROOT=Path(__file__).resolve().parents[1]


def input_summary(number,args):
    result=[]
    for (name,kind),value in zip(SPECS[number].fields,args):
        if kind=='int':summary=str(value)
        elif kind=='tree':summary=f'{sum(x is not None for x in value)} nodes'
        elif kind in ('matrix','chars'):summary=f'{len(value)}x{len(value[0])}'
        elif kind.startswith('ops'):summary=f'{len(value)} operations'
        else:summary=f'length {len(value)}'
        result.append(f'{name}: {summary}')
    return '; '.join(result)


def audit():
    entries=[];start=time.monotonic()
    for p in catalogue():
        n=p['number'];cases,answers,version=prepare(n)
        args=[c['args'] for c in cases]
        encoded=''.join(encode_case(n,a) for a in args)
        assert decode_cases(n,encoded)==args,(n,'input roundtrip')
        for a in args:validate(n,a)
        expected=''.join(encode_answer(n,a) for a in answers)
        assert all(r['ok'] for r in judge_output(n,args,answers,expected)),(n,'output roundtrip')
        rng=random.Random(88000+n);small=EDGES[n]+[random_case(n,rng) for _ in range(32)]
        for a in small:
            validate(n,a);independent=oracle(n,a)
            # Agreement must be mutual where the solution space has choices.
            reference=__import__('judge.reference',fromlist=['solve']).solve(n,a)
            assert accepts(n,a,independent,reference) and accepts(n,a,reference,independent),(n,'oracle mismatch',a)
        counterexample=None
        for i,a in enumerate(args):
            if cases[i]['kind']=='pressure':continue
            bad_output=encode_answer(n,faulty(n,a))
            if not judge_output(n,[a],[answers[i]],bad_output)[0]['ok']:
                counterexample=i+1;break
        assert counterexample is not None,(n,'common error survived')
        # Exercise a real complete EOF reference program under the same runner.
        reference_program=f'''import sys
sys.path.insert(0,{str(ROOT)!r})
from judge.protocols import decode_cases,encode_answer
from judge.reference import solve
for args in decode_cases({n},sys.stdin.read()):
    sys.stdout.write(encode_answer({n},solve({n},args)))
'''
        result=execute(reference_program,encoded,seconds=8)
        assert result['status']=='OK',(n,'real reference run',result['status'],result['stderr'])
        assert all(r['ok'] for r in judge_output(n,args,answers,result['stdout'])),(n,'real reference output')
        # A genuine program that emits only the first result must fail for every
        # problem, proving EOF framing cannot silently accept a single example.
        first_only='import sys\nsys.stdin.read()\nsys.stdout.write('+repr(encode_answer(n,answers[0]))+')'
        first=execute(first_only,''.join(encode_case(n,a) for a in args[:2]))
        assert first['status']=='OK' and not all(r['ok'] for r in judge_output(n,args[:2],answers[:2],first['stdout'])),(n,'EOF omission accepted')
        entry=dict(number=n,title=p['title'],category=p['category'],version=version,groups=len(cases),
                   sample_groups=sum(c['kind']=='sample' for c in cases),
                   boundary_groups=sum(c['kind']=='boundary' for c in cases),
                   random_groups=sum(c['kind']=='random' for c in cases),
                   pressure=[input_summary(n,c['args']) for c in cases if c['kind']=='pressure'],
                   independent_groups=len(small),common_error=LABELS[n],counterexample_group=counterexample,
                   input_sha256=hashlib.sha256(encoded.encode()).hexdigest(),
                   real_program_milliseconds=result['milliseconds'],memory_kb=result['memory_kb'],
                   reference_program_passed=True,eof_omission_rejected=True)
        entries.append(entry)
        if len(entries)%10==0:print(f'Verified {len(entries)}/100',flush=True)
    report=dict(protocol_version='hot100-eof-v2.1',problem_count=len(entries),
                total_groups=sum(e['groups'] for e in entries),independent_groups=sum(e['independent_groups'] for e in entries),
                seconds=round(time.monotonic()-start,2),entries=entries)
    output=ROOT/'docs/judge-coverage.json'
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    lines=['# Hot 100 判题覆盖报告','',
           '由 `python -m judge.audit` 全量验收生成。每题经过合法输入检查、协议往返、独立小规模对照、错误模型拦截、真实 EOF 参考程序运行与遗漏 EOF 反例检查。',
           '',f"共 {len(entries)} 题，固定测试 {report['total_groups']} 组，独立对照 {report['independent_groups']} 组。所有题均通过本次质量门槛，不代表力扣官方隐藏用例或穷尽所有输入。",'',
           '“错误模型”是针对常见算法缺陷的输出模型；此外每题实际运行一个只输出首组答案的错误程序验证 EOF 拒绝。完整源码级错误实现不以此报告冒充。', '',
           '| 题号 | 题目 | 固定组数 | 独立对照 | 上界压力 | 被拦截的错误模型 | 真实程序耗时 |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for e in entries:
        lines.append(f"| {e['number']} | {e['title']} | {e['groups']} | {e['independent_groups']} | {' / '.join(e['pressure'])} | {e['common_error']} | {e['real_program_milliseconds']} ms |")
    lines+=['','固定用例版本及输入哈希、反例组号、内存监控值详见 `judge-coverage.json`。这里的真实程序耗时为单进程全量题目输入的实测；正式提交按多个批次执行，另计进程启动与调度开销。']
    (ROOT/'docs/judge-coverage.md').write_text('\n'.join(lines)+'\n','utf-8')
    print(f"PASS: {len(entries)}/100; {report['total_groups']} groups; {report['independent_groups']} independent; {report['seconds']} seconds",flush=True)
    return report


if __name__=='__main__':audit()
