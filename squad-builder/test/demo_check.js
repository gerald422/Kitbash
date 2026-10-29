// Open the online demo page and count, per step, the cards still tagged "no fit yet"; screenshot the pads step.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !/fonts\.g/.test(m.text())) errs.push('console: ' + m.text()); });
  await page.goto('http://localhost:8771/squad_builder.html');
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 90000 });
  const res = await page.evaluate(() => {
    const sb = window.__sb, out = {};
    Object.keys(sb.SLOT).forEach(k => {
      const sl = sb.SLOT[k];
      const c = sb.candidates(sl);
      out[k] = c.length;
    });
    return {n: sb.S.parts.length, slots: out};
  });
  console.log(JSON.stringify(res));
  // pick a torso, an arm, then look at the pads step's cards
  for (const slot of ['torso', 'legs', 'armR', 'padR', 'shinR']) {
    await page.evaluate((s) => window.__sb.goSlot(s), slot);
    await page.waitForTimeout(400);
    const tags = await page.$$eval('.card .tag', els => els.map(e => e.textContent));
    const flagged = tags.filter(t => t === 'no fit yet').length;
    console.log(slot, 'cards', tags.length, 'no fit yet', flagged);
    if (slot === 'torso' || slot === 'legs' || slot === 'armR') {
      const first = await page.$('.card:not(.on)');
      if (first) { await first.click(); await page.waitForTimeout(800); }
    }
  }
  await page.screenshot({ path: '/home/claude/builder/test/out/demo_check.png' });
  console.log('errors:', errs.length ? errs.slice(0, 5) : 'none');
  await b.close();
})();
