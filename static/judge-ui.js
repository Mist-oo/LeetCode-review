'use strict';
const verdicts={QUEUED:'排队中',RUNNING:'判题中',AC:'全部通过',WA:'答案错误',CE:'语法错误',RE:'运行异常',TLE:'运行超时',MLE:'内存超限',OLE:'输出超限',CANCELLED:'已取消',IE:'判题服务错误',INTERRUPTED:'服务重启中断',DONE:'运行完成'};
const terminalVerdicts=new Set(['AC','WA','CE','RE','TLE','MLE','OLE','CANCELLED','IE','INTERRUPTED','DONE']);
const lastJobs=new Map(), polling=new Set();
let completionEnabled=localStorage.getItem('leetcode-completion')!=='false',completionTimer,creatingJudgment=false;

function showAcm(){
  const spec=current.acm;
  $('#panel').innerHTML=`<h2>ACM 输入输出规范</h2><div class="help-text">${esc(spec.introduction)}</div><h3>每组输入，按顺序读取</h3><ol class="protocol-fields">${spec.fields.map(f=>`<li><strong>${esc(f.name)}</strong><p>${esc(f.description)}</p></li>`).join('')}</ol><h3>每组输出</h3><p>${esc(spec.output)}</p>${spec.details?`<div class="help-text">${esc(spec.details)}</div>`:''}<h3>多组公开样例</h3><p class="muted">不含组数 T，空行可能属于数据，不能随意跳过。</p><h3>输入 <button class="small ghost" id="copy-sample">复制</button></h3><pre class="detail-code">${esc(spec.sample_input)}</pre><h3>输出</h3><pre class="detail-code">${esc(spec.sample_output)}</pre><div class="source-note">协议 ${esc(spec.version)} · 每批默认 ${spec.limits.batch_seconds} 秒 · 内存监控 ${spec.limits.memory_mb} MB · 输出限制 ${spec.limits.output_mb} MB<br>运行本机个人代码；不是安全沙箱。内部原地操作、深拷贝等实现要求由自己检查。</div>`;
  $('#copy-sample').onclick=()=>copyText(spec.sample_input);
}

function setupCompletion(cm){
  const toggle=$('#completion-toggle');toggle.checked=completionEnabled;
  toggle.onchange=()=>{completionEnabled=toggle.checked;localStorage.setItem('leetcode-completion',String(completionEnabled));if(!completionEnabled){cm.closeHint();$('#signature').classList.add('hidden');}};
  const suggest=()=>{
    if(!completionEnabled||editor!==cm)return;
    cm.showHint({hint:()=>completionHints(cm),completeSingle:false});
  };
  cm.addKeyMap({'Ctrl-Space':suggest});
  cm.on('inputRead',()=>{
    clearTimeout(completionTimer);
    if(!completionEnabled)return;
    const pos=cm.getCursor(),token=cm.getTokenAt(pos),line=cm.getLine(pos.line).slice(0,pos.ch);
    if(token.type&&/comment|string/.test(token.type))return;
    if(/[\p{L}_.(,]$/u.test(line))completionTimer=setTimeout(suggest,350);
    else $('#signature')?.classList.add('hidden');
  });
}

async function completionHints(cm){
  const code=cm.getValue(),pos=cm.getCursor(),prefix=cm.getLine(pos.line).slice(0,pos.ch),word=prefix.match(/[\p{L}_][\p{L}\p{N}_]*$/u)?.[0]||'';
  try{
    const result=await api('/complete','POST',{code,line:pos.line+1,column:Array.from(prefix).length});
    const now=cm.getCursor();
    if(editor!==cm||cm.getValue()!==code||!completionEnabled||now.line!==pos.line||now.ch!==pos.ch)return null;
    const signature=$('#signature');
    if(signature){signature.textContent=result.signatures.map(s=>s.text).join(' · ');signature.classList.toggle('hidden',!result.signatures.length);}
    return {list:result.items.map(item=>({text:item.name,displayText:`${item.name}  ·  ${item.type}`})),from:CodeMirror.Pos(pos.line,pos.ch-word.length),to:pos};
  }catch{return null;}
}

function setupJudge(){
  const pid=current.id;
  editor.on('change',()=>{if(lastJobs.has(pid)&&$('#judgment'))renderJudgment(lastJobs.get(pid));});
  $('#judge-card').innerHTML=`<div class="judge-toolbar"><strong>本地 ACM 判题</strong><div class="actions"><button class="small" id="run-code">运行输入</button><button class="small" id="strengthen">随机加强</button><button class="small primary" id="submit-code">提交判题</button><button class="small hidden" id="cancel-job">取消</button></div></div><details class="judge-input"><summary>测试输入 · 默认已填入多组样例</summary><textarea id="test-input" aria-label="ACM 测试输入" spellcheck="false">${esc(current.acm.sample_input)}</textarea><div class="input-actions"><small>可替换为自定义输入；运行不进入提交历史。</small><button class="small ghost" id="reset-input">恢复公开样例</button></div></details><div id="judgment" class="judgment"><p class="muted">先查看左侧 ACM 格式，再编写完整的 EOF 程序。</p></div><details class="submission-history"><summary>正式提交历史 <span id="submission-count"></span></summary><div id="submission-list"></div></details>`;
  $('#reset-input').onclick=()=>$('#test-input').value=current.acm.sample_input;
  $('#run-code').onclick=()=>startJudgment('run');$('#submit-code').onclick=()=>startJudgment('submit');$('#strengthen').onclick=()=>startJudgment('strengthen');
  const cached=lastJobs.get(pid);if(cached){renderJudgment(cached);if(!terminalVerdicts.has(cached.status))pollJudgment(cached.id,pid);}
  refreshSubmissions(pid,true);
}

async function startJudgment(mode,seed){
  if(creatingJudgment)return;
  if(!editor.getValue().trim())return toast('请先编写 Python 程序',true);
  const pid=current.id,code=editor.getValue();
  const stdin=mode==='run'?$('#test-input').value:undefined;
  creatingJudgment=true;
  for(const id of ['run-code','submit-code','strengthen'])$('#'+id).disabled=true;
  $('#judgment').innerHTML='<p class="muted">正在保存草稿并准备本次运行…</p>';
  try{
    await flushDraft();
    const body={code,mode};if(mode==='run')body.stdin=stdin;if(seed!==undefined)body.seed=seed;
    const job=await api(`/problems/${pid}/${mode==='run'?'run':'submit'}`,'POST',body);
    job.code=code;rememberJob(pid,job);renderJudgment(job);pollJudgment(job.id,pid);
  }catch(e){toast(e.message,true);if(current?.id===pid){const previous=lastJobs.get(pid);if(previous)renderJudgment(previous);else{for(const id of ['run-code','submit-code','strengthen'])$('#'+id).disabled=false;$('#judgment').textContent=e.message;}}}
  finally{creatingJudgment=false;}
}

function rememberJob(pid,job){lastJobs.set(pid,job);if(lastJobs.size>10)lastJobs.delete(lastJobs.keys().next().value);}

async function pollJudgment(id,pid){
  if(polling.has(id))return;polling.add(id);
  try{
    while(true){
      const job=await api('/jobs/'+id);rememberJob(pid,job);
      if(current?.id===pid&&$('#judgment'))renderJudgment(job);
      if(terminalVerdicts.has(job.status)){if(current?.id===pid)await refreshSubmissions(pid);break;}
      await new Promise(resolve=>setTimeout(resolve,400));
    }
  }catch(e){if(current?.id===pid)toast('判题状态读取失败，可在提交历史中重新打开：'+e.message,true);}
  finally{polling.delete(id);}
}

function renderJudgment(job){
  const node=$('#judgment');if(!node)return;
  const running=!terminalVerdicts.has(job.status),progress=job.total?Math.round(job.completed/job.total*100):0;
  for(const id of ['run-code','submit-code','strengthen'])$('#'+id).disabled=running;
  $('#cancel-job').classList.toggle('hidden',!running);$('#cancel-job').onclick=async()=>{try{await api(`/jobs/${job.id}/cancel`,'POST',{});}catch(e){toast(e.message,true);}};
  const codeChanged=job.code!==undefined&&editor?.getValue()!==job.code;
  node.innerHTML=`<div class="verdict-row"><strong class="verdict ${job.status==='AC'?'accepted':job.status==='WA'?'wrong':''}">${esc(verdicts[job.status]||job.status)}</strong><span>${job.total?`通过 ${job.passed} / ${job.total} 组`:running?'正在准备测试集…':''}</span></div>${running?`<progress max="100" value="${progress}" aria-label="判题进度"></progress><small>已检查 ${job.completed} 组 · 本机串行运行</small>`:`<small>${job.milliseconds} ms · 监控峰值 ${(job.memory_kb/1024).toFixed(1)} MB${job.seed!==null&&job.seed!==undefined?' · 随机种子 '+job.seed:''}</small>`}<div class="judge-version">${esc(job.version)}${codeChanged?' · 当前代码已修改，旧结果不代表当前代码':''}</div>${job.message?`<pre class="runner-output">${esc(job.message)}</pre>`:''}${job.mode==='run'&&job.detail?`<h4>实际输出</h4><pre class="runner-output">${esc(job.detail.stdout||'（无输出）')}</pre><h4>预期输出</h4><pre class="runner-output">${esc(job.detail.expected)}</pre>${job.detail.stderr?`<h4>异常信息</h4><pre class="runner-output">${esc(job.detail.stderr)}</pre>`:''}`:!running&&['WA','RE','TLE','MLE','OLE'].includes(job.status)&&!job.revealed?'<p class="muted">失败数据已隐藏，先尝试独立定位问题。</p><button class="small" id="reveal-case">揭示首个失败用例</button>':''}${job.revealed&&job.detail?failureHtml(job.detail):''}`;
  if($('#reveal-case'))$('#reveal-case').onclick=async()=>{try{const revealed=await api(`/jobs/${job.id}/reveal`,'POST',{});rememberJob(current.id,revealed);renderJudgment(revealed);}catch(e){toast(e.message,true);}};
  if($('#reproduce-batch'))$('#reproduce-batch').onclick=()=>{$('#test-input').value=job.detail.batch_input;$('.judge-input').open=true;toast('完整失败批次已放入测试输入，包含此前各组以便复现状态错误');};
  if(!running&&job.mode==='strengthen'&&Number.isInteger(job.seed)){
    node.insertAdjacentHTML('beforeend','<button class="small ghost" id="rerun-seed">同种子复测当前代码</button>');
    $('#rerun-seed').onclick=()=>startJudgment('strengthen',job.seed);
  }
}

function failureHtml(detail){
  if(!detail.input)return '';
  const clipped=value=>esc(String(value??'').slice(0,16000))+(String(value??'').length>16000?'\n… 内容较长，使用完整批次重现查看':'' );
  return `<div class="failure-detail"><h4>失败组 ${detail.group} · ${esc(detail.status)}</h4><h4>本组输入</h4><pre class="runner-output">${clipped(detail.input)}</pre><h4>一种合法预期输出</h4><pre class="runner-output">${clipped(detail.expected)}</pre><h4>已解析的实际答案</h4><pre class="runner-output">${clipped(JSON.stringify(detail.actual))}</pre>${detail.error?`<p>${esc(detail.error)}</p>`:''}${detail.stderr?`<pre class="runner-output">${clipped(detail.stderr)}</pre>`:''}<button class="small" id="reproduce-batch">将完整失败批次放入测试输入</button><p class="muted">组间状态错误需连同此前输入复现，多解题的预期输出仅是一种合法答案。</p></div>`;
}

async function refreshSubmissions(pid,restore=false){
  try{
    const history=await api(`/problems/${pid}/submissions`);if(current?.id!==pid||!$('#submission-list'))return;
    $('#submission-count').textContent=`(${history.length})`;
    $('#submission-list').innerHTML=history.length?history.map(j=>`<button class="submission-item" data-submission="${j.id}"><span>${esc(verdicts[j.status]||j.status)} · ${j.passed}/${j.total}${j.mode==='strengthen'?' · 加强':''}</span><small>${new Date(j.created).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai'})}</small></button>`).join(''):'<p class="muted">还没有正式提交。测试运行不会出现在这里。</p>';
    $$('[data-submission]').forEach(button=>button.onclick=()=>showSubmission(button.dataset.submission));
    if(restore&&history.length&&!lastJobs.has(pid)){
      const job=await api('/jobs/'+history[0].id);if(current?.id===pid){rememberJob(pid,job);renderJudgment(job);if(!terminalVerdicts.has(job.status))pollJudgment(job.id,pid);}
    }
  }catch(e){if(current?.id===pid)toast(e.message,true);}
}

async function showSubmission(id){
  try{
    const job=await api('/jobs/'+id);
    openModal('正式提交详情',`<div class="content-meta"><strong>${esc(verdicts[job.status]||job.status)}</strong><span>${job.passed}/${job.total} 组</span></div><p class="muted">${esc(job.version)}</p><pre class="detail-code">${esc(job.code)}</pre><div class="modal-actions"><button id="view-submission-result">查看判题结果</button><button class="primary" id="restore-submission-code">恢复到编辑器</button></div>`);
    $('#view-submission-result').onclick=()=>{modal.close();rememberJob(current.id,job);renderJudgment(job);if(!terminalVerdicts.has(job.status))pollJudgment(job.id,current.id);};
    $('#restore-submission-code').onclick=()=>{if(editor.getValue()!==job.code&&!confirm('使用这次提交的代码替换当前草稿？'))return;editor.setValue(job.code);modal.close();rememberJob(current.id,job);renderJudgment(job);};
  }catch(e){toast(e.message,true);}
}
