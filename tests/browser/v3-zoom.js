async page => {
  if(new URL(page.url()).origin!=='http://127.0.0.1:8766')throw new Error('Isolated QA service on 8766 only');
  page.on('dialog',dialog=>dialog.type()==='beforeunload'?dialog.accept():dialog.dismiss());
  const assert=(value,message)=>{if(!value)throw new Error(message);};
  const open=()=>page.getByRole('button',{name:'1 两数之和',exact:true}).click();
  const size=()=>page.locator('.CodeMirror').evaluate(el=>parseFloat(getComputedStyle(el).fontSize));
  const view=()=>page.evaluate(()=>({width:innerWidth,ratio:devicePixelRatio,scale:visualViewport.scale,body:getComputedStyle(document.body).fontSize}));
  await page.reload();await open();await page.getByRole('button',{name:'恢复默认字号',exact:false}).count();
  await page.locator('#font-reset').click();let checks=0;
  assert(await size()===14,'default');checks++;
  await page.getByRole('button',{name:'增大代码字号',exact:true}).click();
  assert(await size()===15,'increase');checks++;
  await page.getByRole('button',{name:'减小代码字号',exact:true}).click();
  assert(await size()===14,'decrease');checks++;
  const original=await view();
  await page.evaluate(()=>{
    const cm=document.querySelector('.CodeMirror').CodeMirror;
    cm.closeHint();cm.setValue(Array.from({length:180},(_,i)=>`# row ${i} `+'long text '.repeat(30)).join('\n'));
    cm.scrollTo(0,0);
  });
  const box=await page.locator('.CodeMirror').boundingBox();
  await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
  await page.keyboard.down('Control');await page.mouse.wheel(0,-40);await page.keyboard.up('Control');
  await page.waitForFunction(()=>parseFloat(getComputedStyle(document.querySelector('.CodeMirror')).fontSize)>14);
  const zoomed=await size();assert(zoomed>14,'trusted ctrl wheel increases');checks++;
  assert(JSON.stringify(await view())===JSON.stringify(original),'page zoom unchanged');checks++;
  const stored=await page.evaluate(()=>localStorage.getItem('leetcode-editor-font-size'));
  assert(Number(stored)===zoomed,'persisted zoom');checks++;
  await page.mouse.wheel(0,250);
  await page.waitForFunction(()=>document.querySelector('.CodeMirror').CodeMirror.getScrollInfo().top>0);
  assert(await size()===zoomed,'ordinary vertical scroll does not zoom');checks++;
  await page.mouse.wheel(200,0);
  await page.waitForFunction(()=>document.querySelector('.CodeMirror').CodeMirror.getScrollInfo().left>0);
  assert(await size()===zoomed,'ordinary horizontal scroll does not zoom');checks++;
  await page.waitForFunction(()=>document.querySelector('#save-status').textContent==='已保存到本机');
  await page.reload();await open();assert(await size()===zoomed,'reload restores preference');checks++;
  const text=await page.locator('.CodeMirror').evaluate(el=>el.CodeMirror.getValue());
  await page.locator('.CodeMirror').evaluate(el=>{
    for(let i=0;i<30;i++)el.dispatchEvent(new WheelEvent('wheel',{deltaY:-40,ctrlKey:true,bubbles:true,cancelable:true}));
  });
  assert(await size()===28,'maximum');assert(await page.locator('#font-increase').isDisabled(),'max button disabled');checks++;
  await page.locator('.CodeMirror').evaluate(el=>{
    for(let i=0;i<30;i++)el.dispatchEvent(new WheelEvent('wheel',{deltaY:40,ctrlKey:true,bubbles:true,cancelable:true}));
  });
  assert(await size()===10,'minimum');assert(await page.locator('#font-decrease').isDisabled(),'min button disabled');checks++;
  assert(await page.locator('.CodeMirror').evaluate(el=>el.CodeMirror.getValue())===text,'zoom leaves code unchanged');checks++;
  await page.locator('#font-reset').click();assert(await size()===14,'reset');checks++;
  await page.evaluate(()=>localStorage.setItem('leetcode-editor-font-size','not-a-number'));
  await page.reload();await open();assert(await size()===14,'invalid preference falls back');checks++;
  return {checks,passed:true,hardwarePinch:'not verified; real touchpad confirmation required'};
}
