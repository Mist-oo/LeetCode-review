async page => {
  if(new URL(page.url()).origin!=='http://127.0.0.1:8766')throw new Error('Use the isolated QA service on port 8766; never production.');
  const assert = (value,message) => {if(!value)throw new Error(message);};
  await page.locator('.CodeMirror').waitFor();
  await page.locator('#completion-toggle').uncheck();
  const reset = async (text='',selection=null) => {
    await page.evaluate(({text,selection})=>{
      const cm=document.querySelector('.CodeMirror').CodeMirror;
      cm.setValue(text);cm.clearHistory();
      if(selection)cm.setSelection(...selection);else cm.setCursor(cm.lineCount()-1,cm.getLine(cm.lineCount()-1).length);
      cm.focus();
    },{text,selection});
  };
  const state = ()=>page.evaluate(()=>{const cm=document.querySelector('.CodeMirror').CodeMirror;return {text:cm.getValue(),cursor:cm.getCursor()};});
  let checks=0;
  for(const [left,right] of [['(',')'],['[',']'],['{','}'],["'","'"],['"','"']]){
    await reset();await page.keyboard.type(left);
    let s=await state();assert(s.text===left+right&&s.cursor.ch===1,'pair '+left);checks++;
    await page.keyboard.type(right);s=await state();assert(s.text===left+right&&s.cursor.ch===2,'skip '+right);checks++;
    await reset();await page.keyboard.type(left);await page.keyboard.press('Backspace');
    assert((await state()).text==='','delete '+left);checks++;
    await reset('alpha',[{line:0,ch:0},{line:0,ch:5}]);await page.keyboard.type(left);
    assert((await state()).text===left+'alpha'+right,'surround '+left);checks++;
  }
  await reset();await page.keyboard.type('([{}])');assert((await state()).text==='([{}])','nested');checks++;
  await reset();await page.keyboard.type('"""');let s=await state();
  assert(s.text==='""""""'&&s.cursor.ch===3,'triple open');
  await page.keyboard.type('doc"""');assert((await state()).text==='"""doc"""','triple close');checks++;
  await reset('value = ');await page.keyboard.type('[');await page.keyboard.press('Control+z');
  assert((await state()).text==='value = ','undo pair');checks++;
  await reset();await page.keyboard.insertText('print("hello")\nitems = [1, 2]');
  assert((await state()).text==='print("hello")\nitems = [1, 2]','paste unchanged');checks++;
  await reset('text = "a\\"',[{line:0,ch:10},{line:0,ch:10}]);await page.keyboard.type('"');
  assert((await state()).text==='text = "a\\""','escaped quote must insert, not skip');checks++;
  await reset('# comment ');await page.keyboard.type('"');assert((await state()).text==='# comment "','comment quote literal');checks++;
  await reset('text = "ab"',[{line:0,ch:9},{line:0,ch:9}]);await page.keyboard.type("'");
  assert((await state()).text==='text = "a\'b"','other quote inside string literal');checks++;
  await reset('text = "a\'b"',[{line:0,ch:9},{line:0,ch:9}]);await page.keyboard.type("'");
  assert((await state()).text==='text = "a\'\'b"','existing other quote is not a delimiter');checks++;
  await reset();await page.keyboard.type("'''");await page.keyboard.press('Enter');await page.keyboard.type("doc'''");
  assert((await state()).text==="'''\ndoc'''",'multiline single-quote string');checks++;
  await reset('a = 1\nb = 2',[{line:0,ch:0},{line:1,ch:5}]);await page.keyboard.type('(');
  assert((await state()).text==='(a = 1\nb = 2)','multiline selection');checks++;
  await reset();await page.keyboard.type('f"');await page.keyboard.type('{value}');await page.keyboard.type('"');
  assert((await state()).text==='f"{value}"','formatted string with expression');checks++;
  await reset();await page.locator('#completion-toggle').check();
  await page.evaluate(()=>document.querySelector('.CodeMirror').CodeMirror.focus());
  await page.keyboard.type('items = [1, 2]');
  await page.waitForFunction(()=>document.querySelector('#save-status').textContent==='已保存到本机');
  const saved=await (await page.request.get('http://127.0.0.1:8766/api/problems/1')).json();
  assert(saved.draft==='items = [1, 2]','paired code draft saved unchanged');checks++;
  return {checks,passed:true};
}
