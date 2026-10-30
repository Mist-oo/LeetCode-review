async page => {
  if(new URL(page.url()).origin!=='http://127.0.0.1:8766')throw new Error('Isolated QA only');
  const errors=[];page.on('pageerror',error=>errors.push(String(error)));
  await page.reload();
  await page.route('**/api/problems/1/variants',async route=>{await new Promise(resolve=>setTimeout(resolve,800));await route.continue();});
  await page.getByRole('button',{name:'⤨ 随机复习',exact:true}).click();
  await page.getByRole('button',{name:'ACM 格式',exact:true}).click();
  const sample=await (await page.request.get('http://127.0.0.1:8766/api/problems/1/variants')).json();
  await page.waitForFunction(text=>document.querySelector('#panel').innerText.includes(text),sample.versions[0].sample_input.trim());
  await page.getByRole('button',{name:'← 记录矩阵',exact:true}).click();
  const pending=page.waitForResponse(response=>response.url().endsWith('/api/problems/1/variants'));
  await page.getByRole('button',{name:'⤨ 随机复习',exact:true}).click();
  await page.getByRole('button',{name:'← 记录矩阵',exact:true}).click();
  await pending;
  await page.getByRole('button',{name:'⤨ 随机复习',exact:true}).waitFor();
  if(errors.length)throw new Error(errors.join('\n'));
  await page.unroute('**/api/problems/1/variants');
  return {checks:2,passed:true,errors};
}
