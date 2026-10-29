'use strict';
const $ = (q, root=document) => root.querySelector(q);
const $$ = (q, root=document) => [...root.querySelectorAll(q)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const app = $('#app'), modal = $('#modal');
let state, current = null, editor = null, notesDirty = false, draftDirty = false;
let saveTimer, saveQueue = Promise.resolve(), toastTimer, randomMode = false, practiceIds = [];
let filters = {search:'', category:'', seen:''}, selected = new Set(), dateCount = 7;
const noteFields = [['idea','解题思路'],['key_points','关键点'],['precautions','注意事项'],['boundaries','易错边界'],['reference_code','Python 参考代码']];

function toast(message, error=false) {
  const box = $('#toast'); box.textContent=message; box.classList.toggle('error',error); box.style.display='block';
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>box.style.display='none',error?7000:3000);
}
async function api(path, method='GET', body) {
  const response = await fetch('/api'+path, {method, headers:body?{'Content-Type':'application/json'}:{}, body:body?JSON.stringify(body):undefined});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '本地服务暂时不可用');
  return data;
}
function renderMarkdown(value) {
  return DOMPurify.sanitize(marked.parse(value || ''), {FORBID_TAGS:['style','form','input','button','textarea'], FORBID_ATTR:['style','id']});
}
function bindLinks(root) { $$('a',root).forEach(a=>{a.target='_blank';a.rel='noopener noreferrer';}); }
function days(count) {
  return Array.from({length:count},(_,i)=>{
    const day=new Date(state.today+'T12:00:00Z'); day.setUTCDate(day.getUTCDate()-i); return day.toISOString().slice(0,10);
  });
}
function categories() { return [...new Set(state.problems.map(p=>p.category))]; }
function filteredProblems() {
  const query=filters.search.trim().toLowerCase();
  return state.problems.filter(p=>(!filters.category||p.category===filters.category)&&(!filters.seen||(filters.seen==='done'?p.done:!p.done))&&(!query||`${p.number} ${p.title}`.toLowerCase().includes(query)));
}
async function refreshState() { state=await api('/state'); }
function renderHome() {
  current=null; editor=null; draftDirty=false; notesDirty=false;
  const groups=categories();
  app.innerHTML=`<div class="shell"><aside class="sidebar"><div class="brand"><img src="/icon.svg" alt=""><div>拾题<small>LEETCODE REVIEW</small></div></div>
    <button class="nav-btn active" id="all-problems">▦ <span>练习记录</span></button>
    <div class="side-label">按类型练习</div><div class="side-categories">${groups.map(g=>`<button class="category-btn ${filters.category===g?'active':''}" data-category="${esc(g)}"><span>${esc(g)}</span><span>${state.problems.filter(p=>p.category===g).length}</span></button>`).join('')}</div>
    <div class="local-badge"><span class="dot"></span>本地保存 · 只属于你的练习本<br><span style="padding-left:13px">Python / 每天一点，慢慢记住</span></div></aside>
    <main class="main"><div class="topline"><div><div class="eyebrow">YOUR DAILY PRACTICE · V2</div><h1>把做过的题，变成记住的题。</h1><p>Hot 100 · 本地 ACM 判题与复习记录</p></div><div class="actions"><button class="primary" id="random">⤨ 随机复习</button></div></div>
    <section class="hero"><div><h2>不急着刷更多，先把这一题想清楚。</h2><p>按类型梳理思路，或随机抽一道旧题，看看自己还记得多少。</p></div><div class="hero-glyph" aria-hidden="true">{ }</div></section>
    <section class="card"><div class="toolbar"><input class="search" id="search" type="search" placeholder="搜索题号或题目名称" aria-label="搜索题目" value="${esc(filters.search)}">
    <select id="seen" aria-label="筛选练习状态"><option value="">全部状态</option><option value="done" ${filters.seen==='done'?'selected':''}>以前做过</option><option value="new" ${filters.seen==='new'?'selected':''}>还没做过</option></select>
    <button class="small push" id="mark-done" disabled>标记以前做过</button></div>
    <div class="matrix-meta"><span id="matrix-caption"></span><div class="legend"><span>✅ 独立且无错</span><span>❌ 有错或看过提示</span><span>· 未练习</span></div></div>
    <div class="matrix-scroll" id="matrix-scroll"><table class="matrix" id="matrix"></table></div>
    <div class="table-footer"><span>每天每题一条记录 · 点击题名开始练习，点击结果查看详情</span><button class="small ghost" id="older">更早日期 →</button></div></section></main></div>`;
  $('#search').oninput=e=>{filters.search=e.target.value;renderMatrix();};
  $('#seen').onchange=e=>{filters.seen=e.target.value;renderMatrix();};
  $$('.category-btn').forEach(b=>b.onclick=()=>{filters.category=filters.category===b.dataset.category?'':b.dataset.category;renderHome();});
  $('#all-problems').onclick=()=>{filters={search:'',category:'',seen:''};selected.clear();renderHome();};
  $('#random').onclick=()=>startRandom();
  $('#mark-done').onclick=async()=>{
    try { await api('/mark-done','POST',{ids:[...selected]}); selected.clear(); await refreshState();renderHome();toast('已加入随机复习题池，没有生成历史记录'); } catch(e){toast(e.message,true);}
  };
  $('#older').onclick=()=>{dateCount+=14;renderMatrix();$('#matrix-scroll').scrollLeft=$('#matrix-scroll').scrollWidth;};
  renderMatrix();
}
function renderMatrix() {
  $('#no-results')?.remove();
  const problems=filteredProblems(), dates=days(dateCount), index=new Map(state.records.map(r=>[`${r.problem_id}/${r.day}`,r]));
  const table=$('#matrix');
  table.style.minWidth=(327+dateCount*83)+'px';
  $('#matrix-caption').textContent=`${filters.category||'全部类型'} · ${problems.length} 道题目 · ${state.today.replaceAll('-','.')} 今天`;
  table.innerHTML=`<colgroup><col style="width:42px"><col style="width:285px">${dates.map(()=>'<col style="width:83px">').join('')}</colgroup><thead><tr><th class="check"><input type="checkbox" id="select-all" aria-label="选择当前筛选的全部题目" ${problems.length&&problems.every(p=>selected.has(p.id))?'checked':''}></th><th class="title-col">题目 / ${esc(filters.category||'Hot 100')}</th>${dates.map((d,i)=>`<th class="${i===0?'today':''}"><b>${d.slice(5).replace('-',' / ')}</b>${i===0?'今天':new Date(d+'T12:00:00Z').toLocaleDateString('zh-CN',{weekday:'short',timeZone:'Asia/Shanghai'})}</th>`).join('')}</tr></thead><tbody>${problems.map(p=>`<tr><td class="check"><input type="checkbox" class="select-problem" value="${p.id}" aria-label="选择 ${esc(p.title)}" ${selected.has(p.id)?'checked':''}></td><td class="title-col"><button class="problem-name" data-open="${p.id}" title="${esc(p.title)}"><span class="problem-number">${p.number}</span>${esc(p.title)}</button><div class="problem-sub"><span>${esc(p.category)}</span>${p.done?'<span class="seen">· 已做过</span>':''}</div></td>${dates.map((d,i)=>{const r=index.get(`${p.id}/${d}`);return `<td class="${i===0?'today':''}">${r?`<button class="result-cell ${r.result}" data-record="${p.id}/${d}" title="${esc(r.result==='pass'?'独立且无错':(r.tags.join('、')||'有错或看过提示'))}" aria-label="${esc(p.title)} ${d} ${r.result==='pass'?'通过':'未通过'}">${r.result==='pass'?'✅':'❌'}</button>`:i===0?`<button class="result-cell empty" data-open="${p.id}" title="开始今天的练习" aria-label="练习 ${esc(p.title)}">＋</button>`:'<span class="blank-dot">·</span>'}</td>`;}).join('')}</tr>`).join('')}</tbody>`;
  if(!problems.length) table.insertAdjacentHTML('afterend','<div class="empty-state" id="no-results">没有符合条件的题目，试试调整筛选条件。</div>');
  else $('#no-results')?.remove();
  $('#select-all').onchange=e=>{problems.forEach(p=>e.target.checked?selected.add(p.id):selected.delete(p.id));renderMatrix();};
  $$('.select-problem').forEach(c=>c.onchange=()=>{c.checked?selected.add(Number(c.value)):selected.delete(Number(c.value));updateSelection();});
  $$('[data-open]').forEach(b=>b.onclick=()=>openProblem(Number(b.dataset.open),false));
  $$('[data-record]').forEach(b=>b.onclick=()=>{const [id,day]=b.dataset.record.split('/');showRecord(Number(id),day);});
  updateSelection();
}
function updateSelection(){const b=$('#mark-done');b.disabled=!selected.size;b.textContent=selected.size?`标记以前做过 (${selected.size})`:'标记以前做过';}
async function startRandom() {
  const pool=filteredProblems().filter(p=>p.done);
  if(!pool.length) return toast('当前范围还没有已做题，请先勾选题目并标记“以前做过”',true);
  await openProblem(pool[Math.floor(Math.random()*pool.length)].id,true);
}
async function openProblem(id, random=false) {
  try {
    if(!await canLeave())return;
    if(!current) practiceIds=filteredProblems().map(p=>p.id);
    const p=await api('/problems/'+id); current=p; randomMode=random; notesDirty=false; draftDirty=false;
    renderPractice();
  }catch(e){toast(e.message,true);}
}
async function home() {
  if(!await canLeave())return;
  try{await refreshState();renderHome();}catch(e){toast(e.message,true);}
}
function renderPractice() {
  const p=current;
  app.innerHTML=`<main class="practice-page"><header class="practice-top"><button class="ghost" id="back">← 记录矩阵</button><div class="problem-heading"><div class="eyebrow">${randomMode?'RANDOM REVIEW / 随机复习':'FOCUSED PRACTICE / 按题练习'}</div><h1><span class="muted">${p.number}.</span> ${esc(p.title)}</h1></div><a href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">在力扣查看 ↗</a><span class="chip">${p.day.replaceAll('-','.')}</span></header>
    <div class="practice-grid"><section class="card"><div class="tabs"><button class="tab active" data-tab="description">题目</button><button class="tab" data-tab="acm">ACM 格式</button><button class="tab" data-tab="notes">笔记</button><button class="tab" data-tab="history">练习历史</button></div><div class="panel-body" id="panel"></div></section>
    <div><section class="card"><div class="editor-header"><span><strong>Python 3</strong><small>ACM · 多组直到 EOF</small></span><div class="actions"><label class="completion-switch"><input id="completion-toggle" type="checkbox">上下文补全</label><button class="small ghost" id="copy">复制代码 ⧉</button></div></div><textarea id="code" aria-label="Python 代码编辑器"></textarea><div class="editor-footer"><span id="save-status">当天草稿已恢复</span><span>Ctrl+Space 补全 · 不提供解题模板</span></div><div id="signature" class="signature hidden"></div></section>
    <section class="card judge-card" id="judge-card"></section>
    <section class="card result-card"><div class="section-label"><h3>记录这一次练习</h3><small>由你判断，不自动判题</small></div><div class="result-options"><label class="result-option"><input type="radio" name="result" value="pass" ${p.record?.result==='pass'?'checked':''}>✅ 独立完成且无错</label><label class="result-option bad"><input type="radio" name="result" value="fail" ${p.record?.result==='fail'?'checked':''}>❌ 有错 / 看过提示</label></div>
    <div class="error-details ${p.record?.result==='fail'?'':'hidden'}" id="errors"><div class="tag-list" id="tags"></div><div class="add-tag-row"><input id="new-tag" placeholder="添加自定义错误标签" maxlength="50" aria-label="自定义错误标签"><button class="small" id="add-tag">＋ 添加</button></div><textarea id="error-note" placeholder="这次具体错在哪里？（选填）" aria-label="当次错误说明">${esc(p.record?.note||'')}</textarea></div>
    <div class="result-bottom"><small>看过提示或改过错误，即使最后通过也记 ❌</small><button class="primary" id="save-result">保存今日记录</button></div></section>
    <div class="next-row"><span>跳过不产生记录，代码草稿会保留</span><button id="next">${randomMode?'换一题 ⤨':'下一题 →'}</button></div></div></div></main>`;
  editor=CodeMirror.fromTextArea($('#code'),{mode:{name:'python',version:3},lineNumbers:true,screenReaderLabel:'Python 代码编辑器',indentUnit:4,tabSize:4,indentWithTabs:false,extraKeys:{Tab:cm=>cm.replaceSelection('    ','end')},viewportMargin:20});
  editor.setValue(p.draft); editor.on('change',()=>{draftDirty=true;setSaveStatus('正在保存…');clearTimeout(saveTimer);saveTimer=setTimeout(()=>flushDraft().catch(()=>{}),650);});
  $('#back').onclick=home;$('#copy').onclick=()=>copyText(editor.getValue());$('#next').onclick=nextProblem;
  $$('[data-tab]').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
  $$('input[name=result]').forEach(r=>r.onchange=()=>$('#errors').classList.toggle('hidden',r.value!=='fail'));
  $('#save-result').onclick=saveResult;$('#add-tag').onclick=addTag;
  renderTags(p.record?.tags||[]); showDescription();
  setupCompletion(editor);setupJudge();
}
function setSaveStatus(message,error=false){const node=$('#save-status');if(node){node.textContent=message;node.classList.toggle('save-error',error);}}
async function flushDraft() {
  clearTimeout(saveTimer);
  if(!current||!editor||!draftDirty)return saveQueue;
  const snapshot={id:current.id,day:current.day,code:editor.getValue()};
  const save=async()=>{
    try {
      await api(`/problems/${snapshot.id}/draft`,'PUT',snapshot);
      if(current?.id===snapshot.id&&editor?.getValue()===snapshot.code){draftDirty=false;setSaveStatus('已保存到本机');}
    } catch(e) {setSaveStatus('保存失败 · 点击“保存今日记录”重试',true);toast(e.message,true);throw e;}
  };
  saveQueue=saveQueue.catch(()=>{}).then(save);return saveQueue;
}
async function canLeave() {
  if(notesDirty&&!confirm('解题笔记尚未保存，确定离开并放弃本次笔记修改？'))return false;
  try {await flushDraft();return true;}catch{return confirm('草稿尚未保存。建议先复制代码；仍要离开并放弃未保存内容吗？');}
}
function showDescription() {
  $('#panel').innerHTML=`${randomMode?'':`<div class="content-meta"><span class="chip">${esc(current.category)}</span><span>${esc(current.difficulty)}</span><span class="muted">${esc(current.collection)}</span></div>`}${current.description?`<div class="markdown">${renderMarkdown(current.description)}</div>`:'<div class="help-text">这道题尚无本地题面。可以在力扣打开原题，粘贴题目描述、示例与约束后保存。</div>'}<div class="source-note">${current.source.startsWith('https://github.com/doocs/leetcode/')?`题面来源：<a href="${esc(current.source)}">doocs/leetcode</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a><br>仅提取题面，未导入解法。图示可能需要联网加载。`:'题面来源：'+esc(current.source||'待补充')}<br><button class="small ghost" id="edit-description">编辑 / 补充题面</button></div>`;
  bindLinks($('#panel'));$('#edit-description').onclick=showEditDescription;
}
async function switchTab(tab) {
  if($(`.tab[data-tab="${tab}"]`)?.classList.contains('active'))return;
  if(notesDirty&&tab!=='notes'&&!confirm('笔记尚未保存，确定放弃修改？'))return;
  if(tab!=='notes')notesDirty=false;
  $$('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  if(tab==='description')showDescription();
  if(tab==='acm')showAcm();
  if(tab==='notes')showNotes();
  if(tab==='history'){
    const pid=current.id;
    $('#panel').innerHTML='<p class="muted">正在读取练习记录…</p>';
    try {const history=await api(`/problems/${pid}/history`);if(current?.id!==pid||!$('.tab[data-tab="history"]')?.classList.contains('active'))return;
      $('#panel').innerHTML=history.length?history.map(r=>`<button class="history-row" data-day="${r.day}"><span>${r.result==='pass'?'✅':'❌'} ${r.day}<small>${esc(r.tags.join(' · ')||'独立练习记录')}</small></span><span>查看 →</span></button>`).join(''):'<div class="empty-state">还没有正式练习记录。<br>保存今日结果后，会出现在这里。</div>';
      $$('.history-row').forEach(b=>b.onclick=()=>showRecord(pid,b.dataset.day));
    }catch(e){$('#panel').textContent=e.message;}
  }
}
function showNotes() {
  const notes=current.notes;
  $('#panel').innerHTML=`<div class="notes-tools"><small>长期笔记 · 与当次错误独立保存</small><div><button class="small ghost" id="preview-notes">预览</button><button class="small primary" id="save-notes">保存笔记</button></div></div><div id="notes-fields">${noteFields.map(([key,label])=>`<div class="notes-field"><label for="note-${key}">${label}</label><textarea id="note-${key}" data-note="${key}" class="${key==='reference_code'?'reference':''}" placeholder="${key==='reference_code'?'整理一份自己的 Python 解法（选填）':'支持 Markdown 与代码块'}">${esc(notes[key])}</textarea></div>`).join('')}</div><div id="notes-preview" class="markdown hidden"></div>`;
  $$('[data-note]').forEach(t=>t.oninput=()=>notesDirty=true);
  $('#save-notes').onclick=async()=>{
    const values=Object.fromEntries($$('[data-note]').map(t=>[t.dataset.note,t.value]));
    try{await api(`/problems/${current.id}/notes`,'PUT',values);current.notes=values;notesDirty=false;toast('长期笔记已保存');}catch(e){toast(e.message,true);}
  };
  $('#preview-notes').onclick=()=>{
    const preview=$('#notes-preview'), isHidden=preview.classList.contains('hidden');
    preview.innerHTML=noteFields.map(([key,label])=>`<h3>${label}</h3>${key==='reference_code'?`<pre><code>${esc($('#note-'+key).value)}</code></pre>`:renderMarkdown($('#note-'+key).value)||'<p class="muted">尚未填写</p>'}`).join('');
    preview.classList.toggle('hidden',!isHidden);$('#notes-fields').classList.toggle('hidden',isHidden);$('#preview-notes').textContent=isHidden?'继续编辑':'预览';bindLinks(preview);
  };
}
function renderTags(chosen=[]) { $('#tags').innerHTML=state.tags.map(t=>`<label class="tag-option"><input type="checkbox" value="${esc(t)}" ${chosen.includes(t)?'checked':''}>${esc(t)}</label>`).join(''); }
async function addTag() {
  const name=$('#new-tag').value.trim();if(!name)return;
  const chosen=$$('#tags input:checked').map(t=>t.value);
  try{await api('/tags','POST',{name});if(!state.tags.includes(name))state.tags.push(name);renderTags([...chosen,name]);$('#new-tag').value='';}catch(e){toast(e.message,true);}
}
async function saveResult() {
  const result=$('input[name=result]:checked')?.value;
  if(!result)return toast('先选择 ✅ 或 ❌，再保存今日记录',true);
  const b=$('#save-result');b.disabled=true;
  try {
    await flushDraft();
    const data={day:current.day,result,code:editor.getValue(),tags:$$('#tags input:checked').map(t=>t.value),note:$('#error-note').value};
    await api(`/problems/${current.id}/record`,'PUT',data);current.record=data;
    toast('今日记录已保存，矩阵已更新');setSaveStatus('代码和结果已保存');
    await refreshState();
  }catch(e){toast(e.message,true);}finally{b.disabled=false;}
}
async function nextProblem() {
  let pool=randomMode?state.problems.filter(p=>practiceIds.includes(p.id)&&p.done):practiceIds.map(id=>state.problems.find(p=>p.id===id)).filter(Boolean);
  if(!pool.length)return toast('当前范围没有可练习题目',true);
  const id=randomMode?pool[Math.floor(Math.random()*pool.length)].id:pool[(pool.findIndex(p=>p.id===current.id)+1)%pool.length].id;
  await openProblem(id,randomMode);
}
async function copyText(value) {
  try{await navigator.clipboard.writeText(value);toast('代码已复制');}
  catch{toast('浏览器不允许直接复制，请在编辑器中 Ctrl+A、Ctrl+C',true);editor?.focus();}
}
function openModal(title, body) {
  modal.innerHTML=`<div class="modal-head"><h2>${esc(title)}</h2><button class="ghost small" id="close-modal" aria-label="关闭">✕</button></div><div class="modal-body">${body}</div>`;
  $('#close-modal').onclick=()=>modal.close();modal.showModal();
}
async function showRecord(id,day) {
  try {
    const history=await api(`/problems/${id}/history`), record=history.find(r=>r.day===day), p=state.problems.find(p=>p.id===id);
    if(!record)return toast('记录不存在',true);
    openModal(`${record.result==='pass'?'✅':'❌'} ${p.number}. ${p.title}`,`<div class="content-meta"><span>${day}</span>${record.tags.map(t=>`<span class="chip">${esc(t)}</span>`).join('')}</div>${record.judgment?`<div class="help-text">关联判题：${esc(verdicts[record.judgment.status]||record.judgment.status)} · ${record.judgment.passed}/${record.judgment.total} 组<br>${esc(record.judgment.version)}</div>`:'<p class="muted">没有关联相同代码的正式判题结果。</p>'}<h3>当次错误说明</h3><p class="long-note">${esc(record.note||'未填写')}</p><h3>当次 Python 代码</h3><pre class="detail-code">${esc(record.code||'未保存代码')}</pre><div class="modal-actions"><button id="copy-history">复制代码</button>${day===state.today?'<button class="primary" id="edit-today">编辑今日记录</button>':''}</div>`);
    $('#copy-history').onclick=()=>copyText(record.code);
    if($('#edit-today'))$('#edit-today').onclick=()=>{modal.close();openProblem(id,false);};
  }catch(e){toast(e.message,true);}
}
function showEditDescription() {
  openModal('编辑题目描述',`<div class="help-text">ACM 协议由判题题库固定；修改题面不会改变输入输出规范。修改后题面来源会标记为“用户录入”。</div><textarea id="description-edit" style="min-height:350px" aria-label="题目描述">${esc(current.description)}</textarea><div class="modal-actions"><button class="primary" id="save-description">保存题面</button></div>`);
  $('#save-description').onclick=async()=>{const description=$('#description-edit').value;try{await api(`/problems/${current.id}/description`,'PUT',{description});current.description=description;current.source='用户录入';modal.close();showDescription();toast('题面已保存在本机');}catch(e){toast(e.message,true);}};
}
window.addEventListener('beforeunload',e=>{if(draftDirty||notesDirty){e.preventDefault();e.returnValue='';}});
document.addEventListener('visibilitychange',()=>{if(document.hidden)flushDraft().catch(()=>{});});
// Refresh the home calendar after midnight without disturbing an open practice.
setInterval(async()=>{
  if(current||!state||document.hidden)return;
  const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const value=type=>parts.find(p=>p.type===type).value;
  if(`${value('year')}-${value('month')}-${value('day')}`!==state.today){
    try{await refreshState();renderHome();}catch(e){toast(e.message,true);}
  }
},60000);
refreshState().then(renderHome).catch(e=>{app.innerHTML=`<div class="boot"><h2>暂时无法打开本地记录</h2><p>${esc(e.message)}</p><p>请确认 app.py 正在运行，再刷新页面。</p></div>`;});
