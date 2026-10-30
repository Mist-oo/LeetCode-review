'use strict';

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

async function loadFixedReview(context) {
  try {
    const bundle=await api(`/problems/${context.problemId}/variants`);
    if(reviewState!==context||current?.id!==context.problemId)return;
    context.bundle=bundle;
    if(bundle.available)setReviewVariant(context,nextFixedReviewVariant(bundle));
    else context.error='这道题的固定改写还未提供，可主动查看原题继续练习。';
  } catch(error) {
    if(reviewState!==context)return;
    context.error=error.message;
  } finally {
    if(reviewState===context&&current?.id===context.problemId){context.loading=false;updateReviewIdentity();
      if($('.tab[data-tab="description"]')?.classList.contains('active'))showReviewDescription();
      if($('.tab[data-tab="acm"]')?.classList.contains('active'))showAcm();}
  }
}

function showReviewDescription() {
  const context=reviewState;if(!context)return;
  updateReviewIdentity();
  if(context.revealed){
    showOriginalDescription();
    $('#panel').insertAdjacentHTML('afterbegin','<div class="review-toolbar"><span class="chip">原始题面已展开</span><button class="small" id="hide-original">收起原题，返回场景</button></div>');
    $('#hide-original').onclick=()=>{context.revealed=false;showReviewDescription();};
    return;
  }
  const variant=context.variant,bundle=context.bundle;
  const body=variant?`<article class="markdown"><h2>${esc(variant.title)}</h2>${renderMarkdown(variant.statement)}<h3>条件与要求</h3><ul>${bundle.conditions.map(value=>`<li>${esc(value)}</li>`).join('')}</ul><h3>数据范围</h3>${renderMarkdown(bundle.constraints_html)}<h3>改写样例 · 连续两组输入</h3><p class="muted">遵循 ACM 页的字段顺序，读取到 EOF；多解题展示一种合法输出。</p><h3>输入</h3><pre>${esc(variant.sample_input)}</pre><h3>输出</h3><pre>${esc(variant.sample_output)}</pre></article><div class="source-note">场景叙述和示例已改写，核心条件与原约束保持一致。基于公开题面改编，CC BY-SA 4.0；主动查看原题可见完整来源。</div>`:
    `<div class="help-text" role="status">${esc(context.loading?'正在读取场景题面…':context.error||'场景题面暂不可用。')}</div>`;
  $('#panel').innerHTML=`<div class="review-toolbar"><span class="chip">固定改写${variant?' · 场景 '+(bundle.versions.findIndex(v=>v.id===variant.id)+1):''}</span><div class="actions">${variant?'<button class="small" id="next-scenario">换个场景</button>':''}<button class="small" id="reveal-original">查看原题</button></div></div>${body}`;
  // Constraints retain upstream wording; external links must not expose the
  // canonical question identity before the explicit reveal action.
  $$('a',$('#panel')).forEach(link=>link.replaceWith(...link.childNodes));
  $('#reveal-original').onclick=()=>{context.revealed=true;showReviewDescription();};
  if($('#next-scenario'))$('#next-scenario').onclick=()=>{
    setReviewVariant(context,nextFixedReviewVariant(bundle));showReviewDescription();
  };
}
