async page => {
  if(new URL(page.url()).origin!=='http://127.0.0.1:8766')throw new Error('Isolated QA on 8766 only');
  await page.evaluate(()=>localStorage.setItem('leetcode-review-source','fixed'));
  await page.reload();await page.locator('#matrix').waitFor();
  const before=await (await page.request.get('http://127.0.0.1:8766/api/state')).json();
  await page.evaluate(()=>openProblem(1,true));
  await page.locator('#next-scenario').waitFor();
  await page.getByRole('button',{name:'换个场景',exact:true}).click();
  const code=`import sys
lines = iter(sys.stdin.read().splitlines())
for line in lines:
    n = int(line)
    nums = list(map(int, next(lines).split()))
    assert len(nums) == n
    target = int(next(lines))
    seen = {}
    for i, value in enumerate(nums):
        if target - value in seen:
            print(seen[target - value], i)
            break
        seen[value] = i
`;
  await page.locator('.CodeMirror').evaluate((el,code)=>el.CodeMirror.setValue(code),code);
  await page.getByRole('button',{name:'运行输入',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#judgment strong')?.textContent==='运行完成');
  const run=await page.evaluate(()=>lastJobs.get(1));
  if(run.status!=='DONE'||run.passed!==2||run.total!==2)throw new Error('Rewritten EOF examples did not pass');
  await page.getByRole('button',{name:'提交判题',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#judgment strong')?.textContent==='全部通过');
  const formal=await page.evaluate(()=>lastJobs.get(1));
  if(formal.status!=='AC'||formal.passed!==formal.total||formal.total<130)throw new Error('Formal judge regression');
  if(!await page.getByRole('button',{name:'查看原题',exact:true}).isVisible())throw new Error('Judge disclosed original');
  const after=await (await page.request.get('http://127.0.0.1:8766/api/state')).json();
  if(JSON.stringify(before.records)!==JSON.stringify(after.records))throw new Error('Judge changed manual daily results');
  return {checks:4,passed:true,run_groups:run.total,formal_groups:formal.total};
}
