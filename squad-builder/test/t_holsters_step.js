// The library's holsters, pouches and grenades in the Holsters step (Nov 3, plates only): each left file or its right
// mirror variant per side; the Outrider pairs as the maker's own left and right files; none left in the Belt step.
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/pagelib/&libpath=D%3A%5CKitbash%20Library';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL);
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  let fails = 0; const ck = (l, c, d) => { console.log((c ? '  ok   ' : '  FAIL ') + l + (c ? '' : '  ' + JSON.stringify(d))); if (!c) fails++; };
  const ev = (f, a) => page.evaluate(f, a);
  const pick = async (slot, n) => { await ev((s) => window.__sb.goSlot(s), slot); const i = await ev((n) => window.__sb.S.parts.find(p => p.name === n).id, n); await ev((i) => window.__sb.choose(i), i); await page.waitForTimeout(150); };
  await pick('torso', 'MarFil Assault - Torso 1'); await pick('legs', 'MarFil Assault - Legs 4A');
  await pick('plateR', 'MarFil Assault - Hip Plate L'); await pick('plateL', 'MarFil Assault - Hip Plate L');
  const c = await ev(() => { const sb = window.__sb; const f = (k) => sb.candidates(sb.SLOT[k]).map(p => sb.asFor(p, sb.SLOT[k]).name);
    return { L: f('holsL'), R: f('holsR'), belt: ['hipR', 'hipL', 'beltB'].flatMap(k => sb.candidates(sb.SLOT[k]).map(p => p.name)) }; });
  ck('left plate: 6 sheaths + 42 library parts (Outrider right files not; Scroll Grenade hidden)', c.L.length === 48 && !c.L.includes('MarFil Outrider - Holster 1'), c.L.length);
  ck('right plate: 48, the Outrider right files themselves, the rest mirrors', c.R.length === 48 && c.R.includes('MarFil Outrider - Holster 1') && c.R.includes('TN Mk6 Addon - Holster Pistol R') && !c.R.includes('MarFil Outrider - Holster 1 L'), c.R.filter(n => /Outrider|Mk6 Addon - Holster/.test(n)));
  ck('no holsters, pouches or grenades left in the Belt step', !c.belt.some(n => /Holster|Pouch|Grenade|Melta/.test(n) && !/Hip Plate With/.test(n)), c.belt.filter(n => /Holster|Pouch|Grenade|Melta/.test(n) && !/Hip Plate With/.test(n)));
  await pick('holsL', 'TN Mk6 Addon - Holster Pistol'); await pick('holsR', 'MarFil Outrider - Holster 1');
  const r = await ev(() => window.__sb.requestsFor().map(q => [q.name, q.category, q.socket || '']));
  ck('sent as Plate Accessories on their plate sockets', r.some(q => q[0] === 'TN Mk6 Addon - Holster Pistol' && q[1] === 'Plate Accessories' && q[2] === 'Plate Hang L') && r.some(q => q[0] === 'MarFil Outrider - Holster 1' && q[2] === 'Plate Hang R'), r);
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
