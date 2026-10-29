import json
import atexit
import queue
import subprocess
import sys
import threading
from pathlib import Path

from storage import ValidationError, text
from judge.runner import WindowsJob

_slot=threading.BoundedSemaphore(1)
_worker=None
_responses=None
_job=None


def stop_worker():
    global _worker,_job
    if _job:_job.close();_job=None
    if _worker:
        if _worker.poll() is None:_worker.kill()
        _worker.wait(timeout=2)
        _worker.stdin.close();_worker.stdout.close()
        _worker=None


atexit.register(stop_worker)


def ensure_worker():
    global _worker,_responses,_job
    if _worker and _worker.poll() is None:return False
    stop_worker()
    flags={'creationflags':subprocess.CREATE_NO_WINDOW} if sys.platform=='win32' else {}
    _worker=subprocess.Popen([sys.executable,'-I','-X','utf8',str(Path(__file__).with_name('completion_worker.py'))],
                             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',**flags)
    _job=WindowsJob(_worker)
    _responses=queue.Queue();responses=_responses;worker=_worker
    def read_responses():
        try:
            for line in worker.stdout:responses.put(line)
        except (ValueError,OSError):pass
        finally:responses.put(None)
    threading.Thread(target=read_responses,daemon=True).start()
    return True


def complete(data):
    code=text(data,'code',60000)
    line,column=data.get('line'),data.get('column')
    if type(line) is not int or type(column) is not int or not 1<=line<=10000 or not 0<=column<=60000:
        raise ValidationError('补全光标位置无效')
    if not _slot.acquire(blocking=False):
        return dict(items=[],signatures=[],busy=True)
    try:
        cold=ensure_worker()
        _worker.stdin.write(json.dumps(data,ensure_ascii=False)+'\n');_worker.stdin.flush()
        result=_responses.get(timeout=8 if cold else 5)
        if result is None:
            stop_worker()
            return dict(items=[],signatures=[],error='补全服务暂不可用，请检查运行依赖')
        return json.loads(result)
    except queue.Empty:
        stop_worker()
        return dict(items=[],signatures=[],error='本次补全超时')
    except (OSError,ValueError):
        stop_worker()
        return dict(items=[],signatures=[],error='补全服务暂不可用')
    finally:
        _slot.release()
