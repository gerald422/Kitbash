// Adjust: move / turn / snap / seat a placed part on the page and save it as its fit (sockets file text, index in
// memory, corrections log). Run against a served test library (index.json + the previews of the parts used):
//   node t_adjust.js "http://localhost:8777/Squad%20Builder.html?lib=/reallib/" REPO_LIBRARY_DIR [screenshot.png]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/reallib/&libpath=D%3A%5CKitbash%20Library';
const LIB = process.argv[3] || path.join(__dirname, '..', '..', 'library');
const SHOT = process.argv[4] || '';
const walk = d => fs.readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : e.name.endsWith('.sockets.json') ? [path.join(d, e.name)] : []);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL);
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  let fails = 0; const ck = (l, c, d) => { console.log((c ? '  ok   ' : '  FAIL ') + l + (c ? '' : '  ' + JSON.stringify(d))); if (!c) fails++; };
  const ev = (f, a) => page.evaluate(f, a);

  // 1. every sockets file in the repo comes back byte for byte from the page's reader / writer
  const files = walk(LIB); let bad = [];
  for (let i = 0; i < files.length; i += 400) {
    const texts = files.slice(i, i + 400).map(f => fs.readFileSync(f, 'utf8'));
    const r = await ev(ts => ts.map(t => { const bom = t.charCodeAt(0) === 0xFEFF ? '﻿' : '', body = bom ? t.slice(1) : t, nl = body.indexOf('\r\n') >= 0 ? '\r\n' : '\n';
      try { return bom + window.__sb.adj.ljText(window.__sb.adj.ljParse(body), nl) + (/\n$/.test(body) ? nl : '') === t; } catch (e) { return false; } }), texts);
    r.forEach((ok, k) => { if (!ok) bad.push(files[i + k]); });
  }
  ck(`all ${files.length} sockets files round-trip byte for byte`, bad.length === 0, bad.slice(0, 5));

  // 2. writing one fit changes only that fit and "exact"
  const armFile = files.find(f => /MarFil Assault - Arm 1B R\.sockets\.json$/.test(f)), armText = fs.readFileSync(armFile, 'utf8');
  const F = [0.5, -0.8660254, 0, 1.25, 0.8660254, 0.5, 0, -2, 0, 0, 1, 0.00001234, 0, 0, 0, 1];
  const w = await ev(a => { const p = window.__sb.S.parts.find(p => p.name === 'MarFil Assault - Arm 1B R'); return [window.__sb.adj.sidecarWithFit(a.t, p, null, 'Shoulder R', a.F), window.__sb.adj.sidecarWithFit(a.t, p, 0, 'Shoulder L', a.F)]; }, { t: armText, F });
  const A = JSON.parse(armText), B = JSON.parse(w[0]), C = JSON.parse(w[1]);
  ck('the fit is written', B.fits['Shoulder R'].every((x, i) => Math.abs(x - F[i]) < 1e-9) && B.exact.includes('Shoulder R'), B.fits);
  const strip = d => { d = JSON.parse(JSON.stringify(d)); delete d.fits['Shoulder R']; delete d.exact; return d; };
  ck('nothing else in the file changes', JSON.stringify(strip(A)) === JSON.stringify(strip(B)), null);
  const la = armText.split(/\r?\n/), lb = w[0].split(/\r?\n/); const same = lb.filter(l => la.includes(l)).length;
  ck('untouched lines keep their text; floats written as Python does (1.0, 1.234e-05)', lb.length - same <= 22 && /\n\s+1\.0,?\r?\n/.test(w[0]) && w[0].includes('1.234e-05') && (armText.includes('\r\n') === w[0].includes('\r\n')), [lb.length - same]);
  ck("a maker's copy gets it in its own entry", C.variants[0].sidecar.fits['Shoulder L'].every((x, i) => Math.abs(x - F[i]) < 1e-9) && C.variants[0].sidecar.exact.includes('Shoulder L') && JSON.stringify(C.fits) === JSON.stringify(A.fits), null);

  // 3. a model, then adjust the sword in its hand
  const id = n => ev(n => window.__sb.S.parts.find(p => p.name === n).id, n);
  const M = { legs: 'MarFil Assault - Legs 1A', torso: 'MarFil Assault - Torso 1', armR: 'MarFil Assault - Arm 1B R', armL: 'MarFil Assault - Arm 1B R', handR: 'MarFil Assault - Chain Sword 1 R',
    padR: 'MarFil Assault - Shoulder Pad 1', padL: 'MarFil Assault - Shoulder Pad 1', head: 'MarFil Assault - Helmet 1', pack: 'MarFil Assault - Jump Pack 1' };
  const picks = {}; for (const k in M) picks[k] = { id: await id(M[k]) };
  await ev(p => { window.__sb.S.models = [p]; window.__sb.goSlot('legs'); }, picks);
  await page.waitForFunction(() => window.__sb.adj.meshes().length >= 9, null, { timeout: 30000 });
  const W = slot => ev(s => { const i = window.__sb.layout(0).find(x => x.slot === s); return i && i.W ? i.W.elements.slice() : null; }, slot);
  const info = slot => ev(s => { const i = window.__sb.layout(0).find(x => x.slot === s); return i ? { mirror: !!i.as.mirror, v: i.as.v, sock: i.asock, hasSw: !!i.Sw, name: i.as.name } : null; }, slot);
  const dist = (a, b) => Math.hypot(a[12] - b[12], a[13] - b[13], a[14] - b[14]);
  const ang = (a, b) => { const tr = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[4] * b[4] + a[5] * b[5] + a[6] * b[6] + a[8] * b[8] + a[9] * b[9] + a[10] * b[10]; return Math.acos(Math.max(-1, Math.min(1, (tr - 1) / 2))) * 180 / Math.PI; };
  ck('every picked part is placed with a socket to adjust on', (await Promise.all(['legs', 'armR', 'armL', 'handR', 'padR', 'padL', 'head', 'pack'].map(info))).every(x => x && x.hasSw), await info('padL'));
  const nreq = await ev(() => window.__sb.requestsFor().length);
  await page.click('#adjbtn');
  ck('Adjust opens its panel', await page.isVisible('#adj') && (await page.textContent('#adjname')).includes('Click a part'), null);
  await ev(() => window.__sb.adj.select(0, 'torso'));
  ck('a torso cannot be adjusted', /no socket fit/.test(await page.textContent('#status')), await page.textContent('#status'));
  const w0 = await W('handR'), a0 = await W('armR');
  await ev(() => { window.__sb.adj.select(0, 'handR'); const p = window.__sb.adj.pivot(); p.rotateY(20 * Math.PI / 180); p.translateZ(0.5); window.__sb.adj.changed(); });
  const w1 = await W('handR');
  ck('turning the handle turns the sword about its wrist (20 deg, 0.5 mm)', Math.abs(ang(w0, w1) - 20) < 0.01 && Math.abs(dist(w0, await W('handR')) - dist(w0, w1)) < 1e-9 && dist(a0, await W('armR')) < 1e-9, [ang(w0, w1)]);
  ck('the panel shows the change', /turned 20\.0/.test(await page.textContent('#adjdelta')) && /0\.50 mm/.test(await page.textContent('#adjdelta')) && !(await page.isDisabled('#adjsave')), await page.textContent('#adjdelta'));
  await page.click('#adjreset');
  ck('Reset puts it back', dist(w0, await W('handR')) < 1e-9 && ang(w0, await W('handR')) < 1e-6, null);
  await ev(() => { const p = window.__sb.adj.pivot(); p.rotateY(20 * Math.PI / 180); p.translateZ(0.5); window.__sb.adj.changed(); });
  await page.click('#adjsave'); await page.waitForTimeout(200);
  const after = await ev(() => { const S = window.__sb.S, p = S.parts.find(p => p.name === 'MarFil Assault - Chain Sword 1 R'); return { exact: p.exact, log: S.adj.log.slice(-1)[0], pending: !!S.adj.pending }; });
  const w2 = await W('handR');
  ck('Save keeps it there with nothing pending', !after.pending && dist(w1, w2) < 1e-6 && ang(w1, w2) < 1e-4, [dist(w1, w2)]);
  ck('saved as an exact Hand R fit and logged (part, host, before, after, size)', after.exact.includes('Hand R') && after.log.sock === 'Hand R' && /Chain Sword 1 R\.stl$/.test(after.log.part) && /Arm 1B R\.stl$/.test(after.log.host) && Math.abs(after.log.deg - 20) < 0.01 && after.log.before.length === 16, after.log);

  // 4. a mirrored pad: the fit it mirrors is saved, both sides move
  const il = await info('padL'), r0 = await W('padR'), l0 = await W('padL');
  ck('the left pad is the right pad mirrored', il.mirror && il.v == null && il.sock === 'Pad L', il);
  await ev(() => { window.__sb.adj.select(0, 'padL'); const p = window.__sb.adj.pivot(); p.translateX(0.8); p.rotateZ(10 * Math.PI / 180); window.__sb.adj.changed(); });
  const r1 = await W('padR'), l1 = await W('padL');
  ck('moving the left pad moves the right one the same way, mirrored', dist(l0, l1) > 0.5 && Math.abs(dist(l0, l1) - dist(r0, r1)) < 1e-5 && Math.abs(ang(r0, r1) - 10) < 0.01 && Math.abs(ang(l0, l1) - 10) < 0.01 && Math.abs((l1[12] - l0[12]) + (r1[12] - r0[12])) < 0.02, [dist(l0, l1), dist(r0, r1)]);
  await page.click('#adjsave'); await page.waitForTimeout(200);
  const lg = await ev(() => window.__sb.S.adj.log.slice(-1)[0]);
  ck('saved as the Pad R fit; both pads stay', lg.sock === 'Pad R' && dist(l1, await W('padL')) < 1e-6 && dist(r1, await W('padR')) < 1e-6 && ang(r1, await W('padR')) < 1e-4, lg.sock);

  // 5. a maker's left copy keeps its own fit
  const ia = await info('armL');
  await ev(() => { window.__sb.adj.select(0, 'armL'); const p = window.__sb.adj.pivot(); p.translateY(0.3); window.__sb.adj.changed(); });
  const ar1 = await W('armR'); await page.click('#adjsave'); await page.waitForTimeout(200);
  const lv = await ev(() => window.__sb.S.adj.log.slice(-1)[0]);
  ck("the maker's left arm saves into its own entry and the right arm stays", ia.v === 0 && lv.v === 0 && lv.sock === 'Shoulder L' && dist(a0, ar1) < 1e-9, [ia, lv.v, lv.sock]);

  // 6. Seat and Snap, on the preview meshes
  const gap = () => ev(() => { const ms = window.__sb.adj.meshes(), f = s => ms.find(m => m.parent.userData.slot === s), pts = m => { const a = m.geometry.attributes.position.array, o = []; for (let i = 0; i < a.length; i += 3) o.push(new THREE.Vector3(a[i], a[i + 1], a[i + 2]).applyMatrix4(m.matrix)); return o; };
    const P = pts(f('pack')).filter((_, i) => i % 6 === 0), H = pts(f('torso')); let d = 1e9; P.forEach(p => H.forEach(h => { const x = p.distanceToSquared(h); if (x < d) d = x; })); return Math.sqrt(d); });
  const g0 = await gap();
  await ev(() => { window.__sb.adj.select(0, 'pack'); const ms = window.__sb.adj.meshes(), c = s => new THREE.Box3().setFromObject(ms.find(m => m.parent.userData.slot === s).parent).getCenter(new THREE.Vector3());
    window.__sb.adj.nudge(c('pack').sub(c('torso')).normalize().multiplyScalar(4)); });
  await page.waitForTimeout(100); const g1 = await gap();
  await page.click('#adjseat'); await page.waitForTimeout(300); const g2 = await gap();
  ck('Seat brings a pack pulled 4 mm off the back onto it again', g1 > 2.5 && g2 < 0.6, [g0, g1, g2]);
  await page.click('#adjreset'); await page.waitForTimeout(100);
  await ev(() => window.__sb.adj.select(0, 'padR'));
  const s0 = await W('padR');
  await page.click('#adjsnap');
  const moved = await ev(() => { const ms = window.__sb.adj.meshes(), f = s => ms.find(m => m.parent.userData.slot === s); const p1 = new THREE.Vector3(1, 2, 3), p2 = new THREE.Vector3(1.5, 2.2, 3.9);
    window.__sb.adj.snapClick({ object: f('armR'), point: p1 }); const wrong = document.getElementById('status').textContent;
    window.__sb.adj.snapClick({ object: f('padR'), point: p1 }); window.__sb.adj.snapClick({ object: f('armR'), point: p2 }); return wrong; });
  await page.waitForTimeout(100); const s1 = await W('padR');
  ck('Snap: the clicked spot on the part moves to the clicked spot on the model', /selected part first/.test(moved) && Math.abs(s1[12] - s0[12] - 0.5) < 1e-6 && Math.abs(s1[13] - s0[13] - 0.2) < 1e-6 && Math.abs(s1[14] - s0[14] - 0.9) < 1e-6 && ang(s0, s1) < 1e-6, [s1[12] - s0[12], s1[13] - s0[13], s1[14] - s0[14]]);
  await page.click('#adjreset');

  // 7. a real click in the view picks a part; the log replays over a fresh index
  const box = await page.locator('#view canvas').boundingBox(); let picked = null;
  for (const [fx, fy] of [[0.5, 0.5], [0.45, 0.4], [0.55, 0.4], [0.5, 0.65], [0.42, 0.5], [0.58, 0.5]]) {
    await ev(() => { window.__sb.S.adj.sel = null; }); await page.mouse.click(box.x + box.width * fx, box.y + box.height * fy); await page.waitForTimeout(80);
    picked = await ev(() => window.__sb.S.adj.sel && window.__sb.S.adj.sel.slot); if (picked) break;
  }
  ck('clicking a part in the view selects it', !!picked, picked);
  if (SHOT) { await ev(() => window.__sb.adj.select(0, 'handR')); await page.waitForTimeout(300); await page.screenshot({ path: SHOT }); }
  const log = await ev(() => window.__sb.S.adj.log.map(c => JSON.stringify(c)).join('\n'));
  ck('Send is unchanged by all this', (await ev(() => window.__sb.requestsFor().length)) === nreq && nreq === 9, nreq);
  // 8. with a library folder: the sockets file and the log are written (a private browser folder stands in for the library)
  const sword = files.find(f => /MarFil Assault - Chain Sword 1 R\.sockets\.json$/.test(f)), swordText = fs.readFileSync(sword, 'utf8');
  const wrote = await ev(async t => { const S = window.__sb.S, p = S.parts.find(p => p.name === 'MarFil Assault - Chain Sword 1 R'), root = await navigator.storage.getDirectory();
    const segs = p.path.replace(/\.stl$/i, '.sockets.json').split(/[\\\/]/); let d = root; for (const q of segs.slice(0, -1)) d = await d.getDirectoryHandle(q, { create: true });
    const fh = await d.getFileHandle(segs[segs.length - 1], { create: true }), w = await fh.createWritable(); await w.write(t); await w.close();
    S.libHandle = root; window.__sb.adj.select(0, 'handR'); const pv = window.__sb.adj.pivot(); pv.rotateY(-5 * Math.PI / 180); window.__sb.adj.changed(); await window.__sb.adj.save();
    const txt = await (await fh.getFile()).text(); let log = '';
    try { const b = await root.getDirectoryHandle('_builder'); log = await (await (await b.getFileHandle('corrections.jsonl')).getFile()).text(); } catch (e) { log = 'ERR ' + e.message; }
    S.libHandle = null; return { txt, log, status: document.getElementById('status').textContent }; }, swordText);
  const wj = JSON.parse(wrote.txt), wl = wrote.log.trim().split('\n').map(l => JSON.parse(l));
  ck('Save writes the fit into the sockets file in the library', wj.fits['Hand R'].every((x, i) => Math.abs(x - wl[0].after[i]) < 1e-8) && wj.exact.includes('Hand R') && /Blender will place it/.test(wrote.status), wrote.status);
  ck('...and a line in _builder/corrections.jsonl', wl.length === 1 && wl[0].sock === 'Hand R' && Math.abs(wl[0].deg - 5) < 0.01, wl[0]);
  fs.writeFileSync('/tmp/adjust_written.sockets.json', wrote.txt); fs.writeFileSync('/tmp/adjust_before.sockets.json', swordText);
  await page.click('#adjdone');
  ck('Done closes the panel', !(await page.isVisible('#adj')), null);
  await page.reload(); await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  const fresh = await ev(l => { const S = window.__sb.S, p = S.parts.find(p => p.name === 'MarFil Assault - Chain Sword 1 R'), before = p.fits['Hand R'].slice(); window.__sb.adj.replay(l); return [before, p.fits['Hand R'], p.exact || []]; }, log);
  const want = JSON.parse(log.split('\n')[0]);
  ck('the corrections log replays over a fresh index', fresh[0].some((x, i) => Math.abs(x - want.after[i]) > 1e-6) && fresh[1].every((x, i) => Math.abs(x - want.after[i]) < 1e-9) && fresh[2].includes('Hand R'), null);
  ck('no page errors', errs.length === 0, errs);
  console.log(fails ? `FAILS: ${fails}` : 'all passed');
  await b.close(); process.exit(fails ? 1 : 0);
})();
