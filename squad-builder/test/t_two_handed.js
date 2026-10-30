// The Two-handed tab: two-armed pieces only there, they replace both arms, pads/hands follow, what goes to Blender.
// node t_two_handed.js [URL of the page with ?lib=...]   (a served _builder index with the parts below)
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/reallib/&libpath=D%3A%5CKitbash%20Library';
const SHOTS = process.argv[3] || '';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL);
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  let fails = 0; const ck = (l, c, d) => { console.log((c ? '  ok   ' : '  FAIL ') + l + (c ? '' : '  ' + JSON.stringify(d))); if (!c) fails++; };
  const ev = (f, a) => page.evaluate(f, a);
  const st = () => ev(() => window.__sb.S.slot);
  const byName = (n) => ev((n) => window.__sb.S.parts.find(p => p.name === n).id, n);
  const choose = async (n) => { const id = await byName(n); await page.click(`.card[data-id="${id}"]`); await page.waitForTimeout(600); };
  const TWO = new Set(['Two-Handed Guns', 'Two-Handed Melee', 'Heavy Weapons']);

  await ev(() => window.__sb.goSlot('torso')); await choose('MarFil Assault - Torso 3');
  await ev(() => window.__sb.goSlot('armR'));
  const tabs = await page.$$eval('#slotseg button', bs => bs.map(x => x.textContent));
  ck('arms has Right, Left and Two-handed', JSON.stringify(tabs) === '["Right","Left","Two-handed"]', tabs);
  const types = (k) => ev((k) => { const sb = window.__sb; return sb.candidates(sb.SLOT[k]).map(p => p.type); }, k);
  const tR = await types('armR'), tL = await types('armL'), t2 = await types('arm2');
  ck('Right has no two-armed pieces', tR.length && tR.every(t => !TWO.has(t)), tR);
  ck('Left has no two-armed pieces', tL.length && tL.every(t => !TWO.has(t)), tL);
  ck('Two-handed has only two-armed pieces', t2.length > 0 && t2.every(t => TWO.has(t)), t2);

  await choose('MarFil Assault - Arm 1A R');
  await page.click('#slotseg button[data-s="arm2"]');
  ck('the tab opens', (await st()) === 'arm2');
  const n1 = await page.textContent('#pnote');
  ck('says it replaces the arms', /replaces the arms/.test(n1), n1);
  // a hover tries it in place, without the right arm
  const id2 = await byName('MarFil Intercessor - Bolter 5C Grenade');
  await page.hover(`.card[data-id="${id2}"]`); await page.waitForTimeout(800);
  const hv = await ev((id) => window.__sb.layout(0, {slot: 'arm2', part: window.__sb.S.byId[id]}).map(x => x.slot), id2);
  ck('trying it leaves the arms out', hv.includes('arm2') && !hv.includes('armR'), hv);
  await page.click(`.card[data-id="${id2}"]`); await page.waitForTimeout(600);
  let m = await ev(() => Object.keys(window.__sb.S.models[0]));
  ck('picking it removes the arms', m.includes('arm2') && !m.includes('armR') && !m.includes('armL'), m);
  const steps = await page.$eval('.step[data-i="3"]', e => e.innerText);
  ck('the steps show one 2H line', /2H/.test(steps) && !/\nR\n|\nL\n/.test(steps) && /Bolter 5C Grenade/.test(steps), steps);
  // where it goes: the torso's Shoulder R socket . its fit (as before)
  const pos = await ev(() => {
    const sb = window.__sb, L = sb.layout(0), t = L.find(x => x.slot === 'torso'), a = L.find(x => x.slot === 'arm2');
    const s = t.as.data.sockets.find(q => q.t === 'Shoulder R'), f = a.as.data.fits['Shoulder R'];
    const S4 = new THREE.Matrix4(); S4.set.apply(S4, s.m); const F4 = new THREE.Matrix4(); F4.set.apply(F4, f);
    const want = t.W.clone().multiply(S4).multiply(F4);
    return Math.max.apply(null, want.elements.map((v, i) => Math.abs(v - a.W.elements[i])));
  });
  ck('placed on the torso\'s Shoulder R by its fit', pos < 1e-6, pos);
  if (SHOTS) await page.screenshot({ path: SHOTS + '/two_handed_tab.png' });

  // Next: straight on to the head, then pads and hands skipped (no pad spots on two-handed pieces)
  await page.click('#nextbtn'); ck('Next goes to the head', (await st()) === 'head', await st());
  await ev(() => window.__sb.goSlot('pack')); await page.click('#nextbtn');
  ck('pads and both hands skipped: on to shin pads', (await st()) === 'shinR', await st());
  await ev(() => window.__sb.goSlot('padR'));
  const pn = await page.textContent('#pnote');
  ck('the pad step says why', /no pad spots/.test(pn), pn);
  // a pad and a hand picked earlier stay out of what's sent
  await ev(() => { const sb = window.__sb, id = (n) => ({id: sb.S.parts.find(p => p.name === n).id});
    sb.S.models[0].handR = id('MarFil Assault - Plasma Pistol R'); sb.S.models[0].padR = id('MarFil Assault - Shoulder Pad 5'); });
  const reqs = await ev(() => window.__sb.requestsFor().map(r => [r.category, r.socket || '', r.name]));
  ck('sends the torso and the piece on Shoulder R; no pad, no hand', reqs.length === 2 && reqs.some(r => TWO.has(r[0]) && r[1] === 'Shoulder R'), reqs);
  // a pad spot saved on the piece (by hand): the pad goes there
  const padOk = await ev(() => { const sb = window.__sb, m = sb.S.models[0], p = sb.S.byId[m.arm2.id];
    p.sockets = (p.sockets || []).concat([{t: 'Pad R', m: [1,0,0,8, 0,1,0,0, 0,0,1,30, 0,0,0,1]}]);
    const pad = sb.layout(0).find(x => x.slot === 'padR'); const r = sb.requestsFor().some(q => q.socket === 'Pad R');
    p.sockets.pop(); return !!(pad && pad.W) && r; });
  ck('a pad spot saved on the piece takes the pad', padOk);
  // back to single arms: picking one removes the piece
  await ev(() => window.__sb.goSlot('armL'));
  const n2 = await page.textContent('#pnote');
  ck('Left says it replaces the piece', /replaces the two-handed piece/.test(n2), n2);
  await choose('MarFil Assault - Arm 1B L');
  m = await ev(() => Object.keys(window.__sb.S.models[0]));
  ck('picking an arm removes the two-handed piece', m.includes('armL') && !m.includes('arm2'), m);
  const steps2 = await page.$eval('.step[data-i="3"]', e => e.innerText);
  ck('steps back to R and L lines', !/2H/.test(steps2) && /1B L/.test(steps2), steps2);
  const hand = await ev(() => window.__sb.layout(0).find(x => x.slot === 'handR'));
  ck('the earlier hand comes back with the arms (needs a right arm)', hand && /needs arms/.test(hand.note), hand && hand.note);
  // Next from an empty Right goes Left, then Two-handed, then Head
  await ev(() => { const sb = window.__sb; sb.S.models = [{torso: sb.S.models[0].torso}]; sb.goSlot('armR'); });
  const seq = [];
  for (let i = 0; i < 3; i++) { await page.click('#nextbtn'); seq.push(await st()); }
  ck('empty arms: Next goes Left, Two-handed, Head', seq.join() === 'armL,arm2,head', seq);
  // a squad of 3, same part: each model gets it
  await page.fill('#squadn', '3'); await page.dispatchEvent('#squadn', 'change');
  await ev(() => window.__sb.goSlot('arm2')); await choose('TN Mk4 Tactical - Merged Bolter A1 Arm A1');
  const all = await ev(() => window.__sb.S.models.map(x => !!x.arm2 && !x.armR));
  ck('every model in the squad gets it', all.length === 3 && all.every(Boolean), all);
  ck('no page errors', errs.length === 0, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok');
  await b.close();
  process.exit(fails ? 1 : 0);
})();
