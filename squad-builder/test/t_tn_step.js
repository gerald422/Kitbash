// Legs given hip plate spots (TN, Mar Fil Intercessor / Techmarine ...) take the Mar Fil hip plates, buckle and trophies:
// the steps open, the right plate is the mirror variant, every part sits on its host socket by its fit, sent with its socket.
// node t_tn_step.js [URL] [SHOT] ['["torso", "legs", ...]']  (default: TN Mk8 Torso A1 with two TN legs)
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8778/Squad%20Builder.html?lib=/pagelib/&libpath=D%3A%5CKitbash%20Library';
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
  const SET = process.argv[4] ? JSON.parse(process.argv[4]) : ['TN Mk7-8 - Mk8 Torso A1', 'TN Mk10 Assault - Legs A5', 'TN Mk7-8 - Lower A17'];
  await pick('torso', SET[0]);
  for (const legs of SET.slice(1)) {
    await pick('legs', legs);
    ck(legs + ': plates, buckle and trophies open', await ev(() => ['plateR', 'plateL', 'buckle', 'trophyR', 'trophyL'].every(k => !window.__sb.skippable(k))));
    const pR = await ev(() => { const sb = window.__sb; return sb.candidates(sb.SLOT.plateR).map(p => sb.asFor(p, sb.SLOT.plateR).name); });
    ck('the right plate is the mirror variant', JSON.stringify(pR) === '["MarFil Assault - Hip Plate R"]', pR);
    await pick('plateR', 'MarFil Assault - Hip Plate L'); await pick('plateL', 'MarFil Assault - Hip Plate L'); await pick('buckle', 'MarFil Assault - Buckle');
    const r = await ev(() => {
      const sb = window.__sb, L = sb.layout(0), by = {}; L.forEach(x => { by[x.slot] = x; });
      const M = (a) => { const m = new THREE.Matrix4(); m.set.apply(m, a); return m; };
      const diff = (A, B) => Math.max.apply(null, A.elements.map((v, i) => Math.abs(v - B.elements[i])));
      const on = (host, sock, x) => { const s = host.as.data.sockets.find(q => q.t === sock); return host.W.clone().multiply(M(s.m)).multiply(M(x.as.data.fits[sock])); };
      const out = { notes: L.filter(x => x.note).map(x => x.slot + ': ' + x.note), d: {} };
      [['plateR', 'legs', 'Plate R'], ['plateL', 'legs', 'Plate L'], ['buckle', 'legs', 'Buckle']].forEach(([k, h, s]) => {
        const x = by[k]; if (!x || !x.W) { out.d[k] = 'missing'; return; }
        let W = on(by[h], s, x); if (x.as.align) W = W.multiply(x.as.align);
        out.d[k] = diff(W, x.W.clone().multiply(x.as.align ? x.as.align : new THREE.Matrix4()));
      });
      out.reqs = sb.requestsFor().map(q => [q.name, q.category, q.socket || '']);
      return out;
    });
    ck('plates and buckle placed on the legs\' sockets by their fits', Object.values(r.d).every(x => x !== 'missing' && x < 1e-6), r.d);
    ck('no notes', !r.notes.length, r.notes);
    ck('sent with their sockets', r.reqs.some(q => q[1] === 'Hip Plates' && q[2] === 'Plate R') && r.reqs.some(q => q[1] === 'Hip Plates' && q[2] === 'Plate L') &&
       r.reqs.some(q => q[1] === 'Buckles' && q[2] === 'Buckle'), r.reqs);
  }
  if (SHOT) { await ev(() => window.__sb.goSlot('buckle')); await page.waitForTimeout(2500); await page.screenshot({ path: SHOT }); }
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
