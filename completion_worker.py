"""Static analysis worker. Never executes the submitted source."""
import json
import sys

import jedi


def complete(data):
    code=data['code'];line=data['line'];column=data['column']
    script=jedi.Script(code=code)
    completions=script.complete(line,column)
    signatures=script.get_signatures(line,column)
    return dict(items=[dict(name=c.name,type=c.type,description=c.description) for c in completions[:60]],
                signatures=[dict(text=s.to_string(),index=s.index) for s in signatures[:4]])


if __name__=='__main__':
    for line in sys.stdin:
        try:
            result=complete(json.loads(line))
        except (ValueError,KeyError,TypeError,AttributeError):
            result=dict(items=[],signatures=[])
        print(json.dumps(result,ensure_ascii=False),flush=True)
