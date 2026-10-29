// Drive the Squad Builder headless over the demo library: build a 3-model squad
// through the page's own cards, then save what it would send and where it shows
// every part, plus screenshots.  node drive.js OUTDIR
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.argv[2] || '/home/claude/builder/test/out';
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] })
    .catch(() => chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] }));
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !/fonts\.g/.test(m.text())) errs.push('console: ' + m.text()); });
  await page.goto('http://localhost:8766/Squad%20Builder.html?lib=/reallib/&libpath=D%3A%5CKitbash%20Library');
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  console.log('loaded', await page.evaluate(() => window.__sb.S.parts.length));
  const plan = JSON.parse(fs.readFileSync(process.argv[3] || '/home/claude/builder/test/plan.json', 'utf8'));
  const log = [];
  async function pick(slot, name, model) {
    console.log('pick', slot, name, model);
    if (model != null) await page.click(`.mtab[data-m="${model}"]`);
    await page.evaluate((s) => window.__sb.goSlot(s), slot);
    const found = await page.evaluate(([s, n]) => {
      const sb = window.__sb, c = sb.candidates(sb.SLOT[s]).filter(p => p.name === n || sb.asFor(p, sb.SLOT[s]).name === n);
      return c.length ? [c[0].id, c[0].name] : null;
    }, [slot, name]);
    if (!found) { log.push(`MISSING ${slot}: ${name}`); return; }
    const sel = found[0];
    console.log(' found', found); await page.fill('#fq', found[1]); console.log(' filled');
    await page.hover(`.card[data-id="${sel}"]`, {timeout: 20000}); console.log(' hovered');
    await page.waitForTimeout(300);
    await page.click(`.card[data-id="${sel}"]`, {timeout: 20000}); console.log(' clicked');
    await page.fill('#fq', '');
    log.push(`${model == null ? 'all' : 'model ' + (model + 1)} ${slot}: ${name}`);
  }
  await page.fill('#squadn', String(plan.squad)); await page.dispatchEvent('#squadn', 'change');
  for (const [slot, name] of plan.all) await pick(slot, name, null);
  if (plan.each && plan.each.length) {
    await page.click('#samechk');
    for (const [m, slot, name] of plan.each) await pick(slot, name, m);
  }
  await page.waitForTimeout(1500);
  await page.screenshot({ path: OUT + '/squad.png' });
  // hover a card to show the ghost
  await page.evaluate(() => window.__sb.goSlot('armL'));
  await page.waitForTimeout(400);
  const first = await page.$('.card');
  if (first) { await first.hover(); await page.waitForTimeout(1500); await page.screenshot({ path: OUT + '/ghost.png' }); }
  const dump = await page.evaluate(() => {
    const sb = window.__sb;
    return {
      requests: sb.requestsFor(),
      layouts: sb.S.models.map((_m, i) => sb.layout(i).map(x => ({ slot: x.slot, id: x.part.id, path: x.part.path, v: x.as.v, mirror: x.as.mirror,
        W: x.W ? Array.from(x.W.clone().transpose().elements) : null, note: x.note }))),
      models: sb.S.models
    };
  });
  fs.writeFileSync(OUT + '/dump.json', JSON.stringify(dump, null, 1));
  fs.writeFileSync(OUT + '/log.txt', log.concat(errs).join('\n'));
  console.log(log.join('\n')); console.log('errors:', errs.length ? errs.join('\n') : 'none');
  console.log('requests', dump.requests.length);
  await b.close();
})();
