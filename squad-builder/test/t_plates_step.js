// Hip plates, holsters, buckle, tabard and trophy spots (TIOW Inbox 1.17.6): plates on the legs' Plate R / L (the right
// one the mirror variant), sheaths on the plate's Plate Hang, the buckle on Buckle, tabards on the buckle's Tabard, trophies
// on Trophy R / L; all placed by their fits, sent in order with their sockets.
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
  ck('before legs: the holster step waits for a plate', await ev(() => window.__sb.skippable('holsR') && window.__sb.skippable('tabard')));
  await pick('torso', 'MarFil Assault - Torso 1');
  await pick('legs', 'MarFil Assault - Legs 4A');
  ck('Assault legs take plates, a buckle and trophies', await ev(() => ['plateR', 'plateL', 'buckle', 'trophyR', 'trophyL'].every(k => !window.__sb.skippable(k))));
  const cands = await ev(() => { const sb = window.__sb; return { pR: sb.candidates(sb.SLOT.plateR).map(p => sb.asFor(p, sb.SLOT.plateR).name), hL: sb.candidates(sb.SLOT.holsL).length,
    tab: sb.candidates(sb.SLOT.tabard).map(p => p.name), tr: sb.candidates(sb.SLOT.trophyR).map(p => p.name) }; });
  ck('the right plate is the mirror variant', JSON.stringify(cands.pR) === '["MarFil Assault - Hip Plate R"]', cands.pR);
  ck('six sheaths for the left plate', cands.hL === 6, cands.hL);
  ck('tabards: the CyberBrush ones', cands.tab.length === 2 && cands.tab.every(n => /Loinclothe/.test(n)), cands.tab);
  ck('trophies: the Bug Hunters decorations', cands.tr.length === 2 && cands.tr.every(n => /Belt Decoration/.test(n)), cands.tr);
  await pick('plateR', 'MarFil Assault - Hip Plate L'); await pick('plateL', 'MarFil Assault - Hip Plate L');
  await pick('holsR', 'MarFil Assault - Pistol Sheath 3 L'); await pick('holsL', 'MarFil Assault - Pistol Sheath 1 L');
  await pick('buckle', 'MarFil Assault - Buckle'); await pick('tabard', 'CyberBrush Bug Hunters - Loinclothe 1');
  await pick('trophyR', 'CyberBrush Bug Hunters - Belt Decoration 1'); await pick('trophyL', 'CyberBrush Bug Hunters - Belt Decoration 5');
  const r = await ev(() => {
    const sb = window.__sb, L = sb.layout(0), by = {}; L.forEach(x => { by[x.slot] = x; });
    const M = (a) => { const m = new THREE.Matrix4(); m.set.apply(m, a); return m; };
    const diff = (A, B) => Math.max.apply(null, A.elements.map((v, i) => Math.abs(v - B.elements[i])));
    const on = (host, sock, x) => { const s = host.as.data.sockets.find(q => q.t === sock); return host.W.clone().multiply(M(s.m)).multiply(M(x.as.data.fits[sock])); };
    const out = { notes: L.filter(x => x.note).map(x => x.slot + ': ' + x.note), d: {}, v: {} };
    [['plateR', 'legs', 'Plate R'], ['plateL', 'legs', 'Plate L'], ['holsR', 'plateR', 'Plate Hang R'], ['holsL', 'plateL', 'Plate Hang L'],
     ['buckle', 'legs', 'Buckle'], ['tabard', 'buckle', 'Tabard'], ['trophyR', 'legs', 'Trophy R'], ['trophyL', 'legs', 'Trophy L']].forEach(([k, h, s]) => {
      const x = by[k]; if (!x || !x.W) { out.d[k] = 'missing'; return; }
      let W = on(by[h], s, x); if (x.as.align) W = W.multiply(x.as.align);
      out.d[k] = diff(W, x.W.clone().multiply(x.as.align ? x.as.align : new THREE.Matrix4())); out.v[k] = [x.as.v, x.as.name];
    });
    out.reqs = sb.requestsFor().map(q => [q.name, q.category, q.socket || '']);
    return out;
  });
  ck('every part placed on its host socket by its fit', Object.values(r.d).every(x => x === 'missing' ? false : x < 1e-6), r.d);
  ck('right plate and right sheath are the mirror variants, the left ones the files', r.v.plateR[0] === 0 && r.v.holsR[0] === 0 && r.v.plateL[0] === null && r.v.holsL[0] === null, r.v);
  ck('no notes', !r.notes.length, r.notes);
  const order = r.reqs.map(q => q[2]);
  ck('sent in order: plates before sheaths, the buckle before the tabard',
     order.indexOf('Plate R') < order.indexOf('Plate Hang R') && order.indexOf('Plate L') < order.indexOf('Plate Hang L') && order.indexOf('Buckle') < order.indexOf('Tabard'), r.reqs);
  ck('sent with their types', r.reqs.some(q => q[1] === 'Hip Plates' && q[2] === 'Plate R') && r.reqs.some(q => q[1] === 'Plate Accessories' && q[2] === 'Plate Hang L') &&
     r.reqs.some(q => q[1] === 'Tabards' && q[2] === 'Tabard') && r.reqs.some(q => q[1] === 'Trophies' && q[2] === 'Trophy L'), r.reqs);
  const labels = await page.$$eval('.step', es => es.map(e => e.innerText.split('\n')[0]));
  ck('steps: Hip plates, Holsters, Buckle, Tabard after Shin pads', /Shin pads.*Hip plates.*Holsters.*Buckle.*Tabard.*Loincloth.*Belt/s.test(labels.join('|')), labels);
  if (SHOT) { await ev(() => window.__sb.goSlot('tabard')); await page.waitForTimeout(2500); await page.screenshot({ path: SHOT }); }
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
