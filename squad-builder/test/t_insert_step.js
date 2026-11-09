// Chest insert step (TIOW Inbox 1.17.8): only torsos with the spot (MarFil Assault - Torso 2 Insert) take one; the insert
// is placed by its fit on the torso's Chest Insert socket and sent with its type and socket. Run against a served library
// with the merged index (PC index + the inserts delivery).
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
  ck('a torso without the spot skips Chest insert', await ev(() => window.__sb.skippable('insert')));
  await pick('torso', 'MarFil Assault - Torso 2 Insert');
  ck('the insert torso takes one', await ev(() => !window.__sb.skippable('insert')));
  const cands = await ev(() => { const sb = window.__sb; return sb.candidates(sb.SLOT.insert).map(p => p.name); });
  ck('44 chest inserts to pick from', cands.length === 44 && cands.every(n => /^Bits Inserts - /.test(n)), cands.length);
  await pick('insert', 'Bits Inserts - HH GEN3 02');
  const r = await ev(() => {
    const sb = window.__sb, L = sb.layout(0), by = {}; L.forEach(x => { by[x.slot] = x; });
    const M = (a) => { const m = new THREE.Matrix4(); m.set.apply(m, a); return m; };
    const diff = (A, B) => Math.max.apply(null, A.elements.map((v, i) => Math.abs(v - B.elements[i])));
    const x = by.insert, t = by.torso; if (!x || !x.W) return { missing: true };
    const s = t.as.data.sockets.find(q => q.t === 'Chest Insert');
    const W = t.W.clone().multiply(M(s.m)).multiply(M(x.as.data.fits['Chest Insert']));
    return { d: diff(W, x.W), notes: L.filter(y => y.note).map(y => y.slot + ': ' + y.note), reqs: sb.requestsFor().map(q => [q.name, q.category, q.socket || '']) };
  });
  ck('the insert placed on the torso socket by its fit', !r.missing && r.d < 1e-6, r);
  ck('no notes', r.notes && !r.notes.length, r.notes);
  ck('sent with its type and socket', r.reqs && r.reqs.some(q => q[0] === 'Bits Inserts - HH GEN3 02' && q[1] === 'Chest Inserts' && q[2] === 'Chest Insert'), r.reqs);
  await pick('torso', 'MarFil Assault - Torso 1');
  const note = await ev(() => { window.__sb.goSlot('insert'); return document.body.innerText; });
  ck('a torso without the spot says so', /This torso has no chest insert spot \(so far only MarFil Assault - Torso 2 Insert has one\)/.test(note), note.slice(0, 300));
  await pick('torso', 'MarFil Assault - Torso 2 Insert');
  const labels = await page.$$eval('.step', es => es.map(e => e.innerText.split('\n')[0]));
  ck('step: Chest insert after Chest equipment, before Back', /Chest equipment.*Chest insert.*Back/s.test(labels.join('|')), labels);
  if (SHOT) { await ev(() => window.__sb.goSlot('insert')); await page.waitForTimeout(2500); await page.screenshot({ path: SHOT }); }
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
