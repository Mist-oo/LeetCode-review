async page => {
  if(new URL(page.url()).origin!=='http://127.0.0.1:8766')throw new Error('Isolated QA on 8766 only');
  await page.evaluate(()=>localStorage.setItem('leetcode-review-source','fixed'));
  await page.reload();
  await page.locator('#matrix').waitFor();
  const problems=await page.evaluate(()=>state.problems.map(p=>({id:p.id,number:p.number,title:p.title})));
  if(problems.length!==100)throw new Error('Expected Hot 100');
  let checks=0,versions=0;const errors=[];
  page.on('pageerror',error=>errors.push(String(error)));
  for(const problem of problems){
    // The same application entry point used by the matrix/random selector;
    // direct selection here exhausts the catalogue rather than relying on luck.
    await page.evaluate(id=>openProblem(id,true),problem.id);
    await page.waitForFunction(id=>reviewState?.problemId===id&&!reviewState.loading&&reviewState.variant,problem.id);
    const bundle=await (await page.request.get(`http://127.0.0.1:8766/api/problems/${problem.id}/variants`)).json();
    if(!bundle.available||bundle.versions.length!==3)throw new Error(`Missing bundle ${problem.number}`);
    const seen=new Set();
    for(let i=0;i<3;i++){
      const rendered=await page.evaluate(()=>({id:reviewState.variant.id,title:document.querySelector('#practice-title').textContent,
        panel:document.querySelector('#panel').innerText,input:document.querySelector('#test-input').value,
        sample:current.acm.sample_input,output:current.acm.sample_output,revealed:reviewState.revealed,
        linkVisible:document.querySelector('#leetcode-link').getClientRects().length>0,
        identity:!!document.querySelector('#panel .content-meta'),source:document.querySelector('#review-source').value}));
      const variant=bundle.versions.find(v=>v.id===rendered.id);
      if(!variant||seen.has(variant.id))throw new Error(`Rotation ${problem.number}`);seen.add(variant.id);checks++;
      if(rendered.title!==variant.title||rendered.revealed||rendered.linkVisible||rendered.identity||rendered.source!=='fixed')throw new Error(`Identity ${problem.number}`);checks++;
      if(rendered.input!==variant.sample_input||rendered.sample!==variant.sample_input||rendered.output!==variant.sample_output)throw new Error(`Samples ${problem.number}`);checks++;
      if(!rendered.panel.includes('条件与要求')||!rendered.panel.includes('数据范围')||!rendered.panel.includes(variant.title))throw new Error(`Content ${problem.number}`);checks++;
      await page.getByRole('button',{name:'ACM 格式',exact:true}).click();
      if(!(await page.locator('#panel').innerText()).includes(variant.sample_input.trim()))throw new Error(`ACM sample ${problem.number}`);checks++;
      await page.getByRole('button',{name:'题目',exact:true}).click();
      versions++;
      if(i<2)await page.getByRole('button',{name:'换个场景',exact:true}).click();
    }
    await page.getByRole('button',{name:'查看原题',exact:true}).click();
    if(await page.locator('#practice-title').innerText()!==`${problem.number}. ${problem.title}`||!await page.locator('#leetcode-link').isVisible())throw new Error(`Reveal ${problem.number}`);checks++;
    await page.getByRole('button',{name:'收起原题，返回场景',exact:true}).click();
    if(await page.locator('#leetcode-link').isVisible())throw new Error(`Hide ${problem.number}`);checks++;
  }
  if(errors.length)throw new Error(errors.join('\n'));
  return {checks,passed:true,problems:problems.length,versions};
}
