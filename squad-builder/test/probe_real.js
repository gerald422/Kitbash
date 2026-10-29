const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  page.on('pageerror', e => console.log('pageerror: ' + e.message));
  let n404 = 0; page.on('response', r => { if (r.status() >= 400) n404++; });
  await page.goto('http://localhost:8766/Squad%20Builder.html?lib=/reallib/&libpath=D%3A%5CKitbash%20Library');
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  for (const s of ['torso', 'legs', 'armR']) {
    const t = Date.now();
    const r = await page.evaluate((s) => { const sb = window.__sb; sb.goSlot(s); return sb.candidates(sb.SLOT[s]).length; }, s);
    console.log(s, 'candidates', r, (Date.now() - t) + 'ms', '404s so far', n404);
    if (s === 'torso') await page.evaluate(() => { const sb = window.__sb; const c = sb.candidates(sb.SLOT.torso).find(p => p.name === 'MarFil Assault - Torso 3'); sb.choose(c.id); });
    if (s === 'legs') await page.evaluate(() => { const sb = window.__sb; const c = sb.candidates(sb.SLOT.legs).find(p => p.name === 'MarFil Assault - Legs 1A'); sb.choose(c.id); });
  }
  await page.screenshot({ path: 'out_real/probe.png' });
  await b.close();
})();
