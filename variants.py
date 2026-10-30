"""Versioned, bundled review statements. Does not alter judging semantics."""
import argparse
import hashlib
import json
from pathlib import Path

from catalog import catalogue
from judge.protocols import encode_case,judge_output,decode_cases
from judge.reference import solve
from judge.validation import validate

ROOT=Path(__file__).resolve().parent
CONTENT=ROOT/'content'/'variants'
NUMBERS={p['number'] for p in catalogue()}


def validate_bundle(number,bundle):
    def require(condition,message):
        if not condition:raise ValueError(f'变式 {number}: {message}')
    require(number in NUMBERS,'不属于 Hot 100')
    require(isinstance(bundle,dict),'数据必须为对象')
    require(bundle.get('schema')==1 and bundle.get('number')==number,'版本或题号不一致')
    require(isinstance(bundle.get('conditions'),list) and bundle['conditions'] and
            all(isinstance(s,str) and 0<len(s)<=3000 for s in bundle['conditions']),'缺少核心条件')
    require(isinstance(bundle.get('constraints_html'),str) and 0<len(bundle['constraints_html'])<=30000,'缺少数值约束')
    require(isinstance(bundle.get('source'),str) and bundle['source'].startswith('https://github.com/doocs/leetcode/'),'缺少固定题面出处')
    versions=bundle.get('versions')
    require(isinstance(versions,list) and len(versions)==3,'每题必须恰好三个固定版本')
    ids=set();titles=set();statements=set()
    for index,version in enumerate(versions,1):
        require(isinstance(version,dict),'版本必须为对象')
        require(version.get('id')==f'fixed-{number}-{index}','版本标识不稳定')
        for key,maximum in [('title',100),('statement',12000)]:
            require(isinstance(version.get(key),str) and 0<len(version[key].strip())<=maximum,f'{key} 无效')
        ids.add(version['id']);titles.add(version['title']);statements.add(version['statement'])
        examples=version.get('examples')
        require(isinstance(examples,list) and len(examples)==2,'每版本应有两个连续 EOF 样例')
        for args in examples:
            validate(number,args)
        encoded=''.join(encode_case(number,args) for args in examples)
        require(decode_cases(number,encoded)==examples,'样例不满足 EOF 协议往返')
        answers=[solve(number,args) for args in examples]
        expected=version.get('expected_output')
        require(isinstance(expected,str) and all(r['ok'] for r in judge_output(number,examples,answers,expected)),'样例答案不符合判题规则')
    require(len(ids)==len(titles)==len(statements)==3,'版本内容或标识重复')
    return bundle


def fixed_bundle(number,folder=CONTENT):
    if number not in NUMBERS:raise LookupError('题目不属于 Hot 100')
    path=Path(folder)/f'{number}.json'
    if not path.exists():return {'available':False,'versions':[],'number':number,'schema':1}
    bundle=validate_bundle(number,json.loads(path.read_text('utf-8')))
    content_hash=hashlib.sha256(json.dumps(bundle,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:16]
    versions=[]
    for v in bundle['versions']:
        versions.append(dict(id=v['id'],title=v['title'],statement=v['statement'],
                             sample_input=''.join(encode_case(number,args) for args in v['examples']),
                             sample_output=v['expected_output']))
    return dict(available=True,schema=1,number=number,content_version=f'fixed-v1:{content_hash}',
                conditions=bundle['conditions'],constraints_html=bundle['constraints_html'],source=bundle['source'],versions=versions)


def audit(require_all=False):
    available=[];versions=examples=0
    for number in sorted(NUMBERS):
        bundle=fixed_bundle(number)
        if not bundle['available']:continue
        available.append(number);versions+=len(bundle['versions']);examples+=2*len(bundle['versions'])
    unexpected=[p.name for p in CONTENT.glob('*.json') if not p.stem.isdigit() or int(p.stem) not in NUMBERS]
    if unexpected:raise ValueError(f'非 Hot 100 文件: {unexpected}')
    report=dict(available_problems=len(available),expected_problems=100,versions=versions,examples=examples,
                numbers=available,missing=sorted(NUMBERS-set(available)),all_complete=len(available)==100)
    print(json.dumps(report,ensure_ascii=False))
    if require_all and not report['all_complete']:raise SystemExit('固定改写题面尚未全量完成')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--require-all',action='store_true')
    audit(parser.parse_args().require_all)
