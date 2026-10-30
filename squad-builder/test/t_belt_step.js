// The Belt step: four anchors on the legs, parts listed where they have a fit, placed on the legs' anchor, sent with it.
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/reallib/&libpath=D%3A%5CKitbash%20Library';
const SHOT = process.argv[3] || '';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL);
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  let fails = 0; const ck = (l, c, d) => { console.log((c ? '  ok   ' : '  FAIL ') + l + (c ? '' : '  ' + JSON.stringify(d))); if (!c) fails++; };
  const ev = (f, a) => page.evaluate(f, a);
  const id = (n) => ev((n) => window.__sb.S.parts.find(p => p.name === n).id, n);
  const click = async (n) => { await page.click(`.card[data-id="${await id(n)}"]`); await page.waitForTimeout(500); };
  await ev(() => { window.__sb.S.showHidden = true; });     // the scroll plate is on the default hidden list
  await ev(() => window.__sb.goSlot('legs')); await click('MarFil Assault - Legs 1A');
  await ev(() => window.__sb.goSlot('torso')); await click('MarFil Assault - Torso 3');
  await ev(() => window.__sb.goSlot('hipR'));
  const tabs = await page.$$eval('#slotseg button', bs => bs.map(x => x.textContent));
  ck('belt has four anchors', JSON.stringify(tabs) === '["Right hip","Left hip","Front","Back"]', tabs);
  const names = (k) => ev((k) => { const sb = window.__sb; return sb.candidates(sb.SLOT[k]).map(p => p.name); }, k);
  const r = await names('hipR'), l = await names('hipL');
  ck('right hip lists the holster and pouch plates, not the left ones', r.includes('MarFil Jump Captain - Hip Plate With Holster') && r.includes('MarFil Jump Captain - Hip Plate With Pouch') && !r.includes('MarFil Jump Captain - Relic'), r);
  ck('left hip lists the scroll plate and relic', l.includes('MarFil Jump Captain - Hip Plate With Scroll') && l.includes('MarFil Jump Captain - Relic') && !l.includes('MarFil Jump Captain - Hip Plate With Holster'), l);
  await click('MarFil Jump Captain - Hip Plate With Holster');
  await ev(() => window.__sb.goSlot('hipL')); await click('MarFil Jump Captain - Hip Plate With Scroll');
  const pos = await ev(() => {
    const sb = window.__sb, L = sb.layout(0), lg = L.find(x => x.slot === 'legs'), hp = L.find(x => x.slot === 'hipR');
    const s = lg.as.data.sockets.find(q => q.t === 'Hip R'), f = hp.as.data.fits['Hip R'];
    const S4 = new THREE.Matrix4(); S4.set.apply(S4, s.m); const F4 = new THREE.Matrix4(); F4.set.apply(F4, f);
    const want = lg.W.clone().multiply(S4).multiply(F4);
    return Math.max.apply(null, want.elements.map((v, i) => Math.abs(v - hp.W.elements[i])));
  });
  ck('the plate sits on the legs\' Hip R by its fit', pos < 1e-6, pos);
  const steps = await page.$eval('.step[data-i="9"]', e => e.innerText);
  ck('the steps list shows R and L belt lines', /Belt/.test(steps) && /Holster/.test(steps) && /Scroll/.test(steps), steps);
  const reqs = await ev(() => window.__sb.requestsFor().filter(r => r.category === 'Accessories').map(r => [r.name, r.socket]));
  ck('both go to Blender on their anchors', reqs.length === 2 && reqs.some(r => r[1] === 'Hip R') && reqs.some(r => r[1] === 'Hip L'), reqs);
  if (SHOT) await page.screenshot({ path: SHOT });
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
