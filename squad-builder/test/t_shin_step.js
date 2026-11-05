// Legs given shin spots (Marta, Nov 5) take shin pads: both shin steps open, every pad sits on the legs' Shin R/L socket by
// its fit (a mirrored left copy through its align), and is sent with its socket.
// node t_shin_step.js [URL] [SHOT] ['[["torso", "legs", "pad R", "pad L"], ...]']
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
  const SETS = JSON.parse(process.argv[4]);
  for (const [torso, legs, padR, padL] of SETS) {
    await pick('torso', torso); await pick('legs', legs);
    ck(legs + ': both shin steps open', await ev(() => ['shinR', 'shinL'].every(k => !window.__sb.skippable(k))));
    await pick('shinR', padR); await pick('shinL', padL);
    const r = await ev(() => {
      const sb = window.__sb, L = sb.layout(0), by = {}; L.forEach(x => { by[x.slot] = x; });
      const M = (a) => { const m = new THREE.Matrix4(); m.set.apply(m, a); return m; };
      const diff = (A, B) => Math.max.apply(null, A.elements.map((v, i) => Math.abs(v - B.elements[i])));
      const out = { notes: L.filter(x => x.note).map(x => x.slot + ': ' + x.note), d: {} };
      [['shinR', 'Shin R'], ['shinL', 'Shin L']].forEach(([k, s]) => {
        const x = by[k], h = by.legs; if (!x || !x.W) { out.d[k] = 'missing'; return; }
        const sock = h.as.data.sockets.find(q => q.t === s); if (!sock) { out.d[k] = 'no socket'; return; }
        let W = h.W.clone().multiply(M(sock.m)).multiply(M(x.as.data.fits[s])); if (x.as.align) W = W.multiply(x.as.align);
        out.d[k] = diff(W, x.W.clone().multiply(x.as.align ? x.as.align : new THREE.Matrix4()));
      });
      out.reqs = sb.requestsFor().map(q => [q.name, q.category, q.socket || '']);
      return out;
    });
    ck('pads placed on the legs\' Shin sockets by their fits', Object.values(r.d).every(x => typeof x === 'number' && x < 1e-6), r.d);
    ck('no notes', !r.notes.length, r.notes);
    ck('sent with their sockets', r.reqs.some(q => q[1] === 'Knee Pads' && q[2] === 'Shin R') && r.reqs.some(q => q[1] === 'Knee Pads' && q[2] === 'Shin L'), r.reqs);
  }
  if (SHOT) { await ev(() => window.__sb.goSlot('shinR')); await page.waitForTimeout(2500); await page.screenshot({ path: SHOT }); }
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
