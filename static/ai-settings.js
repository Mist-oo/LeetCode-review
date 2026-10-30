'use strict';

async function showAiSettings() {
  let settings={base_url:'',model:'',has_key:false},message='';
  try {settings=await api('/ai/settings');}catch(error){message=error.message;}
  openModal('AI 题面服务设置',`<p class="muted">填写兼容 Chat Completions 的服务地址、模型名和密钥。设置只保存在本机，用于题面改写；代码补全仍使用本地分析。</p>${message?`<p class="error-banner">${esc(message)}</p>`:''}<form id="ai-settings-form"><div class="form-field"><label for="ai-base-url">服务地址（含服务要求的 /v1 等路径）</label><input id="ai-base-url" type="url" maxlength="2000" placeholder="https://服务域名/v1" value="${esc(settings.base_url)}" autocomplete="off"></div><div class="form-field"><label for="ai-model">模型名</label><input id="ai-model" maxlength="200" placeholder="填写服务提供的模型标识" value="${esc(settings.model)}" autocomplete="off"></div><div class="form-field"><label for="ai-api-key">API 密钥</label><input id="ai-api-key" type="password" maxlength="8000" placeholder="${settings.has_key?'已保存；留空保留原密钥':'填写你的 API 密钥'}" autocomplete="new-password"></div><label class="ai-clear-key"><input id="ai-clear-key" type="checkbox">清除已保存的密钥</label><p id="ai-settings-status" role="status" class="muted">${settings.has_key?'密钥已保存，不回显内容。':'尚未保存密钥。'}</p><div class="modal-actions"><button type="button" id="ai-settings-cancel">取消</button><button class="primary" type="submit" id="ai-settings-save">保存到本机</button></div></form>`);
  $('#ai-settings-cancel').onclick=()=>modal.close();
  $('#ai-settings-form').onsubmit=async event=>{
    event.preventDefault();const button=$('#ai-settings-save');button.disabled=true;
    const data={base_url:$('#ai-base-url').value.trim(),model:$('#ai-model').value.trim(),api_key:$('#ai-api-key').value,clear_key:$('#ai-clear-key').checked};
    try {
      await api('/ai/settings','PUT',data);$('#ai-api-key').value='';modal.close();toast('AI 设置已保存到本机');
    } catch(error){$('#ai-settings-status').textContent=error.message;button.disabled=false;}
  };
}
