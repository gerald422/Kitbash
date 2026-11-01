// The Wings step: right and left wings, each placed through the connector it brings (on the pack's Wing Mount);
// only a back with Wing Mounts takes wings; Blender gets the wings (it brings the connectors itself).
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/qlib3/&libpath=D%3A%5CKitbash%20Library';
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
  const pick = async (slot, n) => { await ev((s) => window.__sb.goSlot(s), slot); const i = await id(n); await ev((i) => window.__sb.choose(i), i); await page.waitForTimeout(200); };
  await pick('legs', 'MarFil Assault - Legs 4B');
  await pick('torso', 'TN Mk7-8 - Upper B1');
  await pick('pack', 'MarFil Assault - Jump Pack 1');
  ck('a back without Wing Mounts: the Wings step is skipped', await ev(() => window.__sb.skippable('wingR') && window.__sb.skippable('wingL')));
  await pick('pack', 'TN Mk6 Assault - Jump Pack Universal');
  ck('the TN Mk6 Universal takes wings', await ev(() => !window.__sb.skippable('wingR') && !window.__sb.skippable('wingL')));
  const label = await page.$eval('.step[data-i="6"]', e => e.innerText);
  ck('step 7 is Wings, after Back', /Wings/.test(label), label);
  const names = await ev(() => { const sb = window.__sb; return sb.candidates(sb.SLOT.wingR).map(p => p.name); });
  ck('six Bladecrow wings to pick from', names.length === 6 && names.every(n => /Bladecrow - Wing/.test(n)), names);
  await pick('wingR', 'Bits Bladecrow - Wing 01 Open R');
  await pick('wingL', 'Bits Bladecrow - Wing 03 Upwards R');
  const r = await ev(() => {
    const sb = window.__sb, L = sb.layout(0), by = {}; L.forEach(x => { by[x.slot] = x; });
    const M = (a) => { const m = new THREE.Matrix4(); m.set.apply(m, a); return m; };
    const diff = (A, B) => Math.max.apply(null, A.elements.map((v, i) => Math.abs(v - B.elements[i])));
    const out = { slots: L.map(x => x.slot), notes: L.filter(x => x.note).map(x => x.slot + ': ' + x.note) };
    ['R', 'L'].forEach(s => {
      const pk = by.pack, mt = by['mount' + s], w = by['wing' + s];
      if (!mt || !w || !w.W) { out[s] = 'missing'; return; }
      const ps = pk.as.data.sockets.find(q => q.t === 'Wing Mount ' + s), ms = mt.as.data.sockets.find(q => q.t === 'Wing ' + s);
      const mW = pk.W.clone().multiply(M(ps.m)).multiply(M(mt.as.data.fits['Wing Mount ' + s]));
      const wW = mt.W.clone().multiply(M(ms.m)).multiply(M(w.as.data.fits['Wing ' + s]));
      out[s] = { mount: diff(mW, mt.W), wing: diff(wW, w.W), mountVariant: mt.as.v, wingVariant: w.as.v, mountName: mt.as.name, wingName: w.as.name };
    });
    out.reqs = sb.requestsFor().filter(q => /Wing/.test(q.category)).map(q => [q.name, q.category, q.socket]);
    return out;
  });
  ck('connectors placed on the pack\'s Wing Mounts by their fits', r.R.mount < 1e-6 && r.L.mount < 1e-6, r);
  ck('wings placed on the connectors\' Wing sockets by their fits', r.R.wing < 1e-6 && r.L.wing < 1e-6, r);
  ck('right: the mirrored connector, the wing as its file; left: the connector as its file, the mirrored wing',
     r.R.mountVariant === 0 && r.R.wingVariant === null && r.L.mountVariant === null && r.L.wingVariant === 0, r);
  ck('sent: two wings on Wing R / Wing L, no connectors (Blender brings them)',
     r.reqs.length === 2 && r.reqs.some(q => q[2] === 'Wing R') && r.reqs.some(q => q[2] === 'Wing L' && /Wing 03/.test(q[0])), r.reqs);
  if (SHOT) { await ev(() => window.__sb.goSlot('wingL')); await page.waitForTimeout(1500); await page.screenshot({ path: SHOT }); }
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
