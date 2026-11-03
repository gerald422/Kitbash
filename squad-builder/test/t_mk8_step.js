// Neck guard and Chest equipment steps (TIOW Inbox 1.17.7): only torsos with the spots (Old Style Space Knight MK8)
// take them; the right chest piece is the mirror variant; parts placed by their fits on the torso's sockets; sent with
// their types and sockets. Run against a served library with the merged index (PC index + the MK8 delivery).
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/pagelib/&libpath=D%3A%5CKitbash%20Library';
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
  const pick = async (slot, n) => { await ev((s) => window.__sb.goSlot(s), slot); const i = await id(n); await ev((i) => window.__sb.choose(i), i); await page.waitForTimeout(150); };
  await pick('torso', 'MarFil Assault - Torso 1');
  await pick('legs', 'MarFil Assault - Legs 1');
  ck('a Mar Fil torso skips Neck guard and Chest equipment', await ev(() => ['neckG', 'chestR', 'chestL'].every(k => window.__sb.skippable(k))));
  await pick('torso', 'OldStyle MK8 - Torso A0');
  ck('an MK8 torso takes them', await ev(() => ['neckG', 'chestR', 'chestL'].every(k => !window.__sb.skippable(k))));
  const cands = await ev(() => { const sb = window.__sb; return { cR: sb.candidates(sb.SLOT.chestR).map(p => sb.asFor(p, sb.SLOT.chestR).name),
    cL: sb.candidates(sb.SLOT.chestL).map(p => sb.asFor(p, sb.SLOT.chestL).name), ng: sb.candidates(sb.SLOT.neckG).map(p => p.name) }; });
  ck('five right chest pieces, the mirror variants', cands.cR.length === 5 && cands.cR.every(n => / R$/.test(n)), cands.cR);
  ck('five left chest pieces, the files', cands.cL.length === 5 && cands.cL.every(n => / L$/.test(n)), cands.cL);
  ck('nine neck guards (8 + the collar)', cands.ng.length === 9 && cands.ng.some(n => /Collar/.test(n)), cands.ng);
  await pick('neckG', 'OldStyle MK8 - Neck Guard 2');
  await pick('chestR', 'OldStyle MK8 - Chest Equipment 1 L'); await pick('chestL', 'OldStyle MK8 - Chest Equipment 3 L');
  const r = await ev(() => {
    const sb = window.__sb, L = sb.layout(0), by = {}; L.forEach(x => { by[x.slot] = x; });
    const M = (a) => { const m = new THREE.Matrix4(); m.set.apply(m, a); return m; };
    const diff = (A, B) => Math.max.apply(null, A.elements.map((v, i) => Math.abs(v - B.elements[i])));
    const on = (host, sock, x) => { const s = host.as.data.sockets.find(q => q.t === sock); return host.W.clone().multiply(M(s.m)).multiply(M(x.as.data.fits[sock])); };
    const out = { notes: L.filter(x => x.note).map(x => x.slot + ': ' + x.note), d: {}, v: {} };
    [['neckG', 'torso', 'Neck Guard'], ['chestR', 'torso', 'Chest Equip R'], ['chestL', 'torso', 'Chest Equip L']].forEach(([k, h, s]) => {
      const x = by[k]; if (!x || !x.W) { out.d[k] = 'missing'; return; }
      let W = on(by[h], s, x); if (x.as.align) W = W.multiply(x.as.align);
      out.d[k] = diff(W, x.W.clone().multiply(x.as.align ? x.as.align : new THREE.Matrix4())); out.v[k] = [x.as.v, x.as.name];
    });
    out.reqs = sb.requestsFor().map(q => [q.name, q.category, q.socket || '']);
    return out;
  });
  ck('every part placed on its torso socket by its fit', Object.values(r.d).every(x => x === 'missing' ? false : x < 1e-6), r.d);
  ck('the right chest piece is the mirror variant, the left the file', r.v.chestR[0] === 0 && r.v.chestL[0] === null, r.v);
  ck('no notes', !r.notes.length, r.notes);
  ck('sent with their types and sockets', r.reqs.some(q => q[1] === 'Neck Guards' && q[2] === 'Neck Guard') && r.reqs.some(q => q[1] === 'Chest Equipment' && q[2] === 'Chest Equip R')
     && r.reqs.some(q => q[1] === 'Chest Equipment' && q[2] === 'Chest Equip L'), r.reqs);
  const labels = await page.$$eval('.step', es => es.map(e => e.innerText.split('\n')[0]));
  ck('steps: Neck guard and Chest equipment after Head, before Back', /Head.*Neck guard.*Chest equipment.*Back/s.test(labels.join('|')), labels);
  if (SHOT) { await ev(() => window.__sb.goSlot('chestL')); await page.waitForTimeout(2500); await page.screenshot({ path: SHOT }); }
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
