"""End-to-end all-100 formal-submit verification in a temporary database."""
import json
import statistics
import tempfile
import time
from pathlib import Path

from catalog import catalogue
from storage import Store
from .jobs import Jobs,TERMINAL

ROOT=Path(__file__).resolve().parents[1]


def benchmark():
    results=[]
    with tempfile.TemporaryDirectory(prefix='judge-benchmark-') as folder:
        store=Store(Path(folder)/'test.db');jobs=Jobs(store)
        try:
            for p in store.state()['problems']:
                n=p['number']
                code=f'''import sys
sys.path.insert(0,{str(ROOT)!r})
from judge.protocols import decode_cases,encode_answer
from judge.reference import solve
for args in decode_cases({n},sys.stdin.read()):
    sys.stdout.write(encode_answer({n},solve({n},args)))
'''
                start=time.monotonic();job=jobs.create(p['id'],dict(code=code))
                deadline=start+45
                while time.monotonic()<deadline:
                    result=jobs.get(job['id'])
                    if result['status'] in TERMINAL:break
                    time.sleep(.01)
                assert result['status']=='AC' and result['passed']==result['total'],(n,result,jobs.reveal(job['id']))
                results.append(dict(number=n,groups=result['total'],version=result['version'],
                                    wall_seconds=round(time.monotonic()-start,3),
                                    execution_milliseconds=result['milliseconds'],memory_kb=result['memory_kb']))
                if len(results)%10==0:print(f'Full submit passed {len(results)}/100',flush=True)
        finally:jobs.close()
    seconds=[r['wall_seconds'] for r in results]
    report=dict(problems=len(results),all_ac=True,under_10_seconds=sum(t<10 for t in seconds),
                median_seconds=round(statistics.median(seconds),3),maximum_seconds=max(seconds),results=results)
    (ROOT/'docs/judge-performance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False),flush=True)
    return report


if __name__=='__main__':benchmark()
