"""Bounded execution of personal Python code; explicitly not a security sandbox."""
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import psutil


class WindowsJob:
    """Kill descendants on close, even when the Python parent exits first."""
    def __init__(self, process):
        self.handle = None
        if os.name != 'nt':
            return
        import ctypes
        from ctypes import wintypes
        class Basic(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit',ctypes.c_int64),('PerJobUserTimeLimit',ctypes.c_int64),
                        ('LimitFlags',wintypes.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),
                        ('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',wintypes.DWORD),
                        ('Affinity',ctypes.c_size_t),('PriorityClass',wintypes.DWORD),('SchedulingClass',wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name,ctypes.c_uint64) for name in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
        class Extended(ctypes.Structure):
            _fields_ = [('BasicLimitInformation',Basic),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),
                        ('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];kernel.CreateJobObjectW.restype=wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
        kernel.SetInformationJobObject.restype=wintypes.BOOL
        kernel.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];kernel.AssignProcessToJobObject.restype=wintypes.BOOL
        kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
        handle=kernel.CreateJobObjectW(None,None)
        info=Extended();info.BasicLimitInformation.LimitFlags=0x2000  # KILL_ON_JOB_CLOSE
        if not handle or not kernel.SetInformationJobObject(handle,9,ctypes.byref(info),ctypes.sizeof(info)) or not kernel.AssignProcessToJobObject(handle,wintypes.HANDLE(int(process._handle))):
            if handle:kernel.CloseHandle(handle)
            process.kill();process.wait()
            raise OSError('无法建立 Windows 子进程清理 Job；本次未继续执行')
        self.handle,self.kernel=handle,kernel

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle);self.handle=None


def execute(code, stdin, cancel=None, seconds=3.0, memory_mb=256, output_bytes=16*1024*1024):
    cancel=cancel or threading.Event()
    try:
        compile(code,'submission.py','exec')
    except (SyntaxError,ValueError) as error:
        return dict(status='CE',stdout='',stderr=str(error),milliseconds=0,memory_kb=0)
    if cancel.is_set():
        return dict(status='CANCELLED',stdout='',stderr='',milliseconds=0,memory_kb=0)
    with tempfile.TemporaryDirectory(prefix='leetcode-run-') as folder:
        source=Path(folder)/'submission.py';source.write_text(code,'utf-8')
        input_path=Path(folder)/'input.txt';input_path.write_text(stdin,'utf-8',newline='')
        stdout,stderr=bytearray(),bytearray();lock=threading.Lock();overflow=threading.Event()
        tracked={};job=None;process=None;status='OK';peak=0;start=time.monotonic()
        def read_stream(stream,target):
            try:
                while chunk:=stream.read1(8192):
                    with lock:
                        remaining=output_bytes-len(stdout)-len(stderr)
                        target.extend(chunk[:max(0,remaining)])
                        if len(chunk)>remaining:overflow.set()
            except (ValueError,OSError):
                pass
            finally:
                stream.close()
        try:
            with input_path.open('rb') as input_file:
                options={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}
                process=subprocess.Popen([sys.executable,'-I','-S','-B','-X','utf8',str(source)],
                    cwd=folder,stdin=input_file,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                    env={k:v for k,v in os.environ.items() if k in ('SystemRoot','WINDIR','TEMP','TMP','PATH','LANG')},**options)
                job=WindowsJob(process)
                root=psutil.Process(process.pid);tracked[root.pid]=root
                threads=[threading.Thread(target=read_stream,args=(process.stdout,stdout),daemon=True),
                         threading.Thread(target=read_stream,args=(process.stderr,stderr),daemon=True)]
                for thread in threads:thread.start()
                while process.poll() is None:
                    if cancel.is_set():status='CANCELLED';break
                    if overflow.is_set():status='OLE';break
                    if time.monotonic()-start>seconds:status='TLE';break
                    try:
                        children=root.children(recursive=True)
                        for child in children:tracked[child.pid]=child
                        memory=sum(p.memory_info().rss for p in [root,*children] if p.is_running())
                        peak=max(peak,memory)
                        if memory>memory_mb*1024*1024:status='MLE';break
                    except (psutil.NoSuchProcess,psutil.AccessDenied):
                        pass
                    cancel.wait(.015)
                # Closing the Job / killing the session also removes any child
                # that outlived a normally exited parent and still holds pipes.
                if job:job.close()
                if os.name!='nt':
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                for child in reversed(list(tracked.values())):
                    try:
                        if child.is_running():child.kill()
                    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                process.wait(timeout=2)
                for thread in threads:thread.join(timeout=2)
                if overflow.is_set() and status=='OK':status='OLE'
                if process.returncode and status=='OK':status='RE'
        except (OSError,subprocess.SubprocessError) as error:
            status='IE';stderr.extend(str(error).encode('utf-8'))
        finally:
            if job:job.close()
            if process and process.poll() is None:
                process.kill();process.wait(timeout=2)
        return dict(status=status,stdout=stdout.decode('utf-8',errors='replace').replace('\r\n','\n'),stderr=stderr.decode('utf-8',errors='replace').replace('\r\n','\n'),
                    milliseconds=round((time.monotonic()-start)*1000),memory_kb=peak//1024)
