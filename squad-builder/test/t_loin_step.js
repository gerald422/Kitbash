// The Loincloth step: loincloths are their own type, the only thing on the belt's front anchor; the Belt step no longer
// has a front tab and lists no loincloths. Hidden loincloths (an aquila on CyberBrush's 3) stay out.
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/qlib2/&libpath=D%3A%5CKitbash%20Library';
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
  const click = async (n) => { const i = await id(n); await ev((i) => window.__sb.choose(i), i); await page.waitForTimeout(300); };
  const names = (k) => ev((k) => { const sb = window.__sb; return sb.candidates(sb.SLOT[k]).map(p => p.name); }, k);
  await ev(() => window.__sb.goSlot('legs')); await click('MarFil Assault - Legs 4B');
  await ev(() => window.__sb.goSlot('torso')); await click('TN Mk7-8 - Upper B1');
  await ev(() => window.__sb.goSlot('loin'));
  const label = await page.$eval('.step[data-i="9"]', e => e.innerText);
  ck('step 10 is Loincloth, before Belt', /Loincloth/.test(label), label);
  const loin = await names('loin');
  const all = await ev(() => window.__sb.S.parts.filter(p => p.type === 'Loincloths').map(p => p.name));
  ck('26 loincloths are their own type', all.length === 26, all.length);
  ck('the step lists them all but the hidden one (aquila on CyberBrush 3)', loin.length === 25 && loin.every(n => /Loincloth/.test(n)) && !loin.includes('CyberBrush Bug Hunters - Loinclothe 3'), loin);
  ck('CyberBrush loincloths have a fit now', loin.includes('CyberBrush Bug Hunters - Loinclothe 1') && (await ev(() => window.__sb.S.parts.find(p => p.name === 'CyberBrush Bug Hunters - Loinclothe 1').fits['Belt Front'])) != null);
  await click('CyberBrush Bug Hunters - Loinclothe 1');
  const pos = await ev(() => {
    const sb = window.__sb, L = sb.layout(0), lg = L.find(x => x.slot === 'legs'), lc = L.find(x => x.slot === 'loin');
    const s = lg.as.data.sockets.find(q => q.t === 'Belt Front'), f = lc.as.data.fits['Belt Front'];
    const S4 = new THREE.Matrix4(); S4.set.apply(S4, s.m); const F4 = new THREE.Matrix4(); F4.set.apply(F4, f);
    const want = lg.W.clone().multiply(S4).multiply(F4);
    return Math.max.apply(null, want.elements.map((v, i) => Math.abs(v - lc.W.elements[i])));
  });
  ck('it sits on the legs\' Belt Front by its fit', pos < 1e-6, pos);
  if (SHOT) await page.screenshot({ path: SHOT });
  await ev(() => window.__sb.goSlot('hipR'));
  const tabs = await page.$$eval('#slotseg button', bs => bs.map(x => x.textContent));
  ck('Belt: right hip, left hip and back only', JSON.stringify(tabs) === '["Right hip","Left hip","Back"]', tabs);
  const belt = [...await names('hipR'), ...await names('hipL'), ...await names('beltB')];
  ck('no loincloths among the belt bits', !belt.some(n => /Loincloth/i.test(n)), belt.filter(n => /Loincloth/i.test(n)));
  await click('TN Mk10 Assault - Jump Pack Accessories 9');
  const reqs = await ev(() => window.__sb.requestsFor().filter(r => /Loincloth|Accessories 9/.test(r.name)).map(r => [r.name, r.category, r.socket]));
  ck('sent: the loincloth as Loincloths on Belt Front, the bit on Hip R',
     reqs.some(r => r[1] === 'Loincloths' && r[2] === 'Belt Front') && reqs.some(r => r[1] === 'Accessories' && r[2] === 'Hip R'), reqs);
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
