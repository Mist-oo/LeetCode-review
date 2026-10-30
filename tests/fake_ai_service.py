"""Loopback-only provider fixture for browser QA, never use real credentials."""
import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,status,value):
        raw=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
        self.end_headers()
        try:self.wfile.write(raw)
        except OSError:pass

    def do_GET(self):
        if self.path=='/stats':
            with self.server.lock:value=dict(calls=self.server.calls,generations=self.server.generations,mode=self.server.mode)
            return self.send(200,value)
        self.send(404,{})

    def do_POST(self):
        data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
        if self.path=='/control':
            mode=data.get('mode','success')
            if mode not in ('success','fail-review','http-error','slow'):return self.send(400,{})
            with self.server.lock:self.server.mode=mode
            return self.send(200,dict(mode=mode))
        if self.path!='/v1/chat/completions':return self.send(404,{})
        with self.server.lock:
            self.server.calls+=1;mode=self.server.mode
        if mode=='http-error':return self.send(503,dict(error='controlled fake provider failure'))
        review='复核员' in data['messages'][0]['content']
        if review:result=dict(equivalent=mode!='fail-review',issues=[] if mode!='fail-review' else ['模拟：新增了条件'])
        else:
            if mode=='slow':time.sleep(.8)
            with self.server.lock:self.server.generations+=1;index=self.server.generations
            result=dict(title=f'AI 两笔收支场景 {index}',statement=f'第 {index} 批审计记录按原始录入顺序保存整数金额，其中可能有冲销负数。给定一个合计金额，请定位唯一两条不同记录，使金额相加恰好等于目标；输出这两个记录位置，顺序不限。',
                        condition_ids=[1,2],examples=[[[4,6,9],10],[[8,-3,2],5]])
        self.send(200,dict(choices=[dict(finish_reason='stop',message=dict(content=json.dumps(result,ensure_ascii=False)))]))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8767);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.lock=threading.Lock();server.calls=0;server.generations=0;server.mode='success'
    print(f'Fake AI test service: http://127.0.0.1:{server.server_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
