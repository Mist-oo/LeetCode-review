"""Write-only API key settings scoped to the selected local database."""
import json
import threading
from pathlib import Path
from urllib.parse import urlsplit

from storage import ValidationError,text


def service_url(value):
    value=value.strip().rstrip('/')
    if not value:return ''
    if len(value)>2000 or any(c.isspace() for c in value):raise ValidationError('服务地址格式不正确')
    try:
        parsed=urlsplit(value);port=parsed.port
    except ValueError:raise ValidationError('服务地址格式不正确') from None
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValidationError('请填写不含账号、参数或片段的 API 地址')
    local=parsed.hostname in ('localhost','127.0.0.1','::1')
    if parsed.scheme!='https' and not (local and parsed.scheme=='http'):
        raise ValidationError('远程服务地址需要 HTTPS；本机服务可使用 HTTP')
    if port is not None and not 1<=port<=65535:raise ValidationError('服务端口不正确')
    return value


class AISettings:
    def __init__(self,path):
        self.path=Path(path);self.lock=threading.RLock()

    def _read(self):
        if not self.path.exists():return dict(base_url='',model='',api_key='')
        try:
            if self.path.stat().st_size>40000:raise ValueError()
            data=json.loads(self.path.read_text('utf-8'))
            if not isinstance(data,dict) or data.get('schema')!=1:raise ValueError()
            if not all(isinstance(data.get(k),str) for k in ('base_url','model','api_key')):raise ValueError()
            return {k:data[k] for k in ('base_url','model','api_key')}
        except (ValueError,UnicodeError):raise ValidationError('本机 AI 设置无法读取，请重新填写并保存') from None

    def public(self):
        with self.lock:
            data=self._read()
            return dict(base_url=data['base_url'],model=data['model'],has_key=bool(data['api_key']),
                        configured=all(data.values()),protocol='chat-completions')

    def credentials(self):
        with self.lock:return self._read()

    def save(self,data):
        with self.lock:
            try:previous=self._read()
            except ValidationError:
                if data.get('api_key') or data.get('clear_key') is True:previous={}
                else:raise
            if 'clear_key' in data and type(data['clear_key']) is not bool:raise ValidationError('清除密钥选项格式不正确')
            base=service_url(text(data,'base_url',2000).strip())
            model=text(data,'model',200).strip()
            key=text(data,'api_key',8000).strip() or previous.get('api_key','')
            if data.get('clear_key'):key=''
            if any(ord(c)<32 for c in model) or any(not 33<=ord(c)<=126 for c in key):
                raise ValidationError('模型名或密钥含不支持的字符')
            value=dict(schema=1,base_url=base,model=model,api_key=key)
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temporary=self.path.with_name(self.path.name+'.tmp')
            temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')
            temporary.replace(self.path)
            return self.public()

    def endpoint(self):
        data=self.credentials()
        if not all(data.values()):raise ValidationError('请先配置 AI 服务地址、模型名和密钥')
        base=service_url(data['base_url'])
        return base if base.endswith('/chat/completions') else base+'/chat/completions'
