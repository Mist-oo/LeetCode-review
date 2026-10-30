'use strict';
const aiReviewRequests=new Map();

function reviewSourcePreference() {
  try{return localStorage.getItem('leetcode-review-source')==='ai'?'ai':'fixed';}catch{return 'fixed';}
}

function nextFixedReviewVariant(bundle) {
  const key='leetcode-fixed-variant-cycles';let cycles={};
  try {
    const saved=JSON.parse(localStorage.getItem(key)||'{}');
    if(saved&&typeof saved==='object'&&!Array.isArray(saved))cycles=saved;
  } catch {}
  const previous=cycles[bundle.number];
  const index=previous?.version===bundle.content_version&&Number.isInteger(previous.index)&&previous.index>=0&&previous.index<bundle.versions.length?
    (previous.index+1)%bundle.versions.length:0;
  cycles[bundle.number]={version:bundle.content_version,index};
  try {localStorage.setItem(key,JSON.stringify(cycles));}catch{}
  return bundle.versions[index];
}

function updateReviewIdentity() {
  if(!randomMode||!reviewState||current?.id!==reviewState.problemId||!$('#practice-title'))return;
  $('#practice-title').textContent=reviewState.revealed?`${current.number}. ${current.title}`:(reviewState.variant?.title||'场景练习');
  $('#leetcode-link').classList.toggle('hidden',!reviewState.revealed);
}

function setReviewVariant(context,variant) {
  if(reviewState!==context||current?.id!==context.problemId)return;
  const previous=current.acm.sample_input;
  context.variant=variant;
  current.acm.sample_input=variant.sample_input;current.acm.sample_output=variant.sample_output;
  if($('#test-input')?.value===previous)$('#test-input').value=variant.sample_input;
  updateReviewIdentity();
}

function refreshReviewPanels(context) {
  if(reviewState!==context||current?.id!==context.problemId)return;
  updateReviewIdentity();
  if($('.tab[data-tab="description"]')?.classList.contains('active'))showReviewDescription();
  if($('.tab[data-tab="acm"]')?.classList.contains('active'))showAcm();
}

function fixedReviewFallback(context) {
  if(!context.bundle?.available)return;
  if(!context.variant?.id.startsWith('fixed-'))setReviewVariant(context,nextFixedReviewVariant(context.bundle));
}

async function loadFixedReview(context) {
  let useAI=false;
  try {
    const bundle=await api(`/problems/${context.problemId}/variants`);
    if(reviewState!==context||current?.id!==context.problemId)return;
    context.bundle=bundle;
    if(bundle.available){
      if(context.source==='ai')useAI=true;
      else setReviewVariant(context,nextFixedReviewVariant(bundle));
    } else context.error='这道题的固定改写还未提供，可主动查看原题继续练习。';
  } catch(error) {
    if(reviewState!==context)return;
    context.error=error.message;
  } finally {
    if(reviewState===context){context.loading=false;refreshReviewPanels(context);}
  }
  if(useAI&&reviewState===context&&context.source==='ai')loadAIReview(context);
}

function requestAIReview(pid,force) {
  if(aiReviewRequests.has(pid))return aiReviewRequests.get(pid);
  const pending=api(`/problems/${pid}/ai-variant`,'POST',{force}).finally(()=>{
    if(aiReviewRequests.get(pid)===pending)aiReviewRequests.delete(pid);
  });
  aiReviewRequests.set(pid,pending);return pending;
}

async function loadAIReview(context,force=false) {
  if(reviewState!==context||context.source!=='ai'||!context.bundle?.available)return;
  const request=++context.request;context.aiLoading=true;context.error='';
  refreshReviewPanels(context);
  const isCurrent=()=>reviewState===context&&current?.id===context.problemId&&context.source==='ai'&&context.request===request;
  try {
    const variant=await requestAIReview(context.problemId,force);
    if(!isCurrent())return;
    if(variant.contract_version!==context.bundle.content_version)throw new Error('AI 题面与当前条件版本不一致，请重新进入本题后重试');
    setReviewVariant(context,variant);
  } catch(error) {
    if(!isCurrent())return;
    context.error=error.message;fixedReviewFallback(context);
  } finally {
    if(isCurrent()){context.aiLoading=false;refreshReviewPanels(context);}
  }
}

function reviewToolbar(context) {
  const variant=context.variant,isAI=variant?.id.startsWith('ai-');
  const index=variant&&!isAI?context.bundle?.versions.findIndex(v=>v.id===variant.id)+1:0;
  const actual=context.revealed?'原始题面已展开':context.aiLoading?'AI 处理中':isAI?(variant.cached?'AI 缓存':'AI 新生成'):variant?`固定改写 · 场景 ${index}`:'等待场景题面';
  return `<div class="review-toolbar"><label class="review-source-label">题面来源<select id="review-source" aria-label="题面来源"><option value="fixed" ${context.source==='fixed'?'selected':''}>固定改写</option><option value="ai" ${context.source==='ai'?'selected':''}>AI 生成</option></select></label><span class="chip" id="review-source-status">${esc(actual)}</span><div class="actions">${context.source==='ai'?`<button class="small" id="review-ai-settings">服务设置</button><button class="small" id="regenerate-review" ${context.aiLoading||context.loading?'disabled':''}>换个说法</button>`:variant?'<button class="small" id="next-scenario">换个场景</button>':''}<button class="small" id="reveal-original">${context.revealed?'收起原题，返回场景':'查看原题'}</button></div></div>`;
}

function bindReviewToolbar(context) {
  $('#review-source').onchange=event=>{
    context.source=event.target.value;context.request++;context.revealed=false;context.error='';context.aiLoading=false;
    try {localStorage.setItem('leetcode-review-source',context.source);}catch{}
    if(context.source==='fixed'){
      fixedReviewFallback(context);refreshReviewPanels(context);
    } else {
      refreshReviewPanels(context);if(context.bundle?.available)loadAIReview(context);
    }
  };
  $('#reveal-original').onclick=()=>{context.revealed=!context.revealed;showReviewDescription();};
  if($('#next-scenario'))$('#next-scenario').onclick=()=>{setReviewVariant(context,nextFixedReviewVariant(context.bundle));showReviewDescription();};
  if($('#review-ai-settings'))$('#review-ai-settings').onclick=showAiSettings;
  if($('#regenerate-review'))$('#regenerate-review').onclick=()=>{context.revealed=false;loadAIReview(context,true);};
}

function showReviewDescription() {
  const context=reviewState;if(!context)return;
  updateReviewIdentity();
  const variant=context.variant,bundle=context.bundle,isAI=variant?.id.startsWith('ai-');
  const status=`${context.source==='ai'?'<p class="review-cost-note">优先复用已检查缓存；主动生成新版本通常包含生成与复核两次模型请求，可能产生服务费用。</p>':''}${context.aiLoading?`<div class="help-text" role="status">正在读取 AI 缓存或生成并检查题面…${variant?'下方暂时保留上一版内容。':''}</div>`:''}${context.error?`<div class="error-banner" role="status">${context.source==='ai'?(variant?.id.startsWith('fixed-')?'AI 未采用，当前展示固定改写。原因：':'AI 题面暂不可用。原因：'):''}${esc(context.error)}${context.source==='ai'?' 可调整服务设置后点击“换个说法”重试。':''}</div>`:''}`;
  if(context.revealed){
    showOriginalDescription();$('#panel').insertAdjacentHTML('afterbegin',reviewToolbar(context)+status);
    bindReviewToolbar(context);return;
  }
  const body=variant?`<article class="markdown"><h2>${esc(variant.title)}</h2>${renderMarkdown(variant.statement)}<h3>条件与要求</h3><ul>${bundle.conditions.map(value=>`<li>${esc(value)}</li>`).join('')}</ul><h3>数据范围</h3>${renderMarkdown(bundle.constraints_html)}<h3>改写样例 · 连续两组输入</h3><p class="muted">遵循 ACM 页的字段顺序，读取到 EOF；多解题展示一种合法输出。</p><h3>输入</h3><pre>${esc(variant.sample_input)}</pre><h3>输出</h3><pre>${esc(variant.sample_output)}</pre></article><div class="source-note">${isAI?`AI 模型：${esc(variant.model)}。${esc(variant.validation)}。<br>`:''}场景叙述和示例已改写，核心条件与原约束保持一致。基于公开题面改编，CC BY-SA 4.0；主动查看原题可见完整来源。</div>`:
    `<div class="help-text" role="status">${esc(context.loading?'正在读取场景题面…':context.aiLoading?'AI 题面检查完成后会在这里显示。':context.error?'可查看原题继续练习。':'场景题面暂不可用。')}</div>`;
  $('#panel').innerHTML=reviewToolbar(context)+status+body;
  $$('a',$('#panel')).forEach(link=>link.replaceWith(...link.childNodes));
  bindReviewToolbar(context);
}
