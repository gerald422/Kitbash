// The armour dropdown (Josh, Nov 9): Tacticus (all power armour), Terminator or Gravis; parts listed only for that
// armour (bases, belt bits and Bits for all); switching takes off what doesn't fit; picks left without a spot after a
// torso or legs swap are taken off and never sent. Run against a served library with the PC's index.
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/pagelib/&libpath=D%3A%5CKitbash%20Library';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL);
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  let fails = 0; const ck = (l, c, d) => { console.log((c ? '  ok   ' : '  FAIL ') + l + (c ? '' : '  ' + JSON.stringify(d))); if (!c) fails++; };
  const ev = (f, a) => page.evaluate(f, a);
  const id = (n) => ev((n) => window.__sb.S.parts.find(p => p.name === n).id, n);
  const pick = async (slot, n) => { await ev((s) => window.__sb.goSlot(s), slot); const i = await id(n); await ev((i) => window.__sb.choose(i), i); await page.waitForTimeout(100); };
  const marks = (slot) => ev((s) => { const sb = window.__sb, c = sb.candidates(sb.SLOT[s]), m = {}; c.forEach(p => { const a = sb.armourOf(p) || 'any'; m[a] = (m[a] || 0) + 1; }); return m; }, slot);
  ck('starts on Tacticus', await ev(() => window.__sb.S.armour === 'Tacticus' && document.getElementById('armour').value === 'Tacticus'));
  const tt = await marks('torso'), tl = await marks('legs'), tb = await marks('base');
  ck('Tacticus: only Tacticus torsos and legs', Object.keys(tt).join() === 'Tacticus' && Object.keys(tl).join() === 'Tacticus', [tt, tl]);
  ck('the thicc legs are not Tacticus any more', !(await ev(() => window.__sb.candidates(window.__sb.SLOT.legs).some(p => /Thicc Legs 3 Knelling/.test(p.name)))));
  // Charny's model: MK8 torso with chest equipment and collar, then a TN torso
  await pick('torso', 'OldStyle MK8 - Torso A0'); await pick('legs', 'MarFil Assault - Legs 1');
  await pick('chestR', 'OldStyle MK8 - Chest Equipment 1 L'); await pick('neckG', 'OldStyle MK8 - Neck Guard Collar');
  ck('on the MK8 torso: chest piece and collar picked', await ev(() => !!(window.__sb.S.models[0].chestR && window.__sb.S.models[0].neckG)));
  await pick('torso', 'TN Mk2 - Upper A1');
  const st = await page.$eval('#status', e => e.innerText).catch(() => '');
  ck('swapping to a TN torso takes them off', await ev(() => !window.__sb.S.models[0].chestR && !window.__sb.S.models[0].neckG), await ev(() => window.__sb.S.models[0]));
  ck('and says so', /Taken off \(no spot for them now\): .*Chest Equipment 1.*Collar|Taken off.*Collar.*Chest/.test(st), st);
  ck('nothing without a spot is sent', await ev(() => window.__sb.requestsFor().every(q => !/Chest Equipment|Neck Guard/.test(q.category))));
  // switching armour
  await ev(() => window.__sb.setArmour('Terminator'));
  ck('Terminator: the Tacticus picks come off', await ev(() => !window.__sb.S.models[0].torso && !window.__sb.S.models[0].legs), await ev(() => window.__sb.S.models[0]));
  const mt = await marks('torso'), ml = await marks('legs'), mb = await marks('base');
  ck('Terminator: only Terminator torsos and legs (incl. the moved thicc ones)', Object.keys(mt).join() === 'Terminator' && Object.keys(ml).join() === 'Terminator'
     && await ev(() => window.__sb.candidates(window.__sb.SLOT.legs).some(p => /Thicc Legs 3 Knelling/.test(p.name))), [mt, ml]);
  await pick('torso', 'Marta Gurls - Termi Torso 1'); await pick('legs', 'Marta Feb 2026 - Thicc Legs 3 Knelling');
  // no Terminator or Gravis torso has sockets yet (Nov 9): the picks stay and go to Blender, to be placed there
  ck('Terminator picks stay and are sent', await ev(() => { const q = window.__sb.requestsFor().map(r => r.name); return q.includes('Marta Gurls - Termi Torso 1') && q.includes('Marta Feb 2026 - Thicc Legs 3 Knelling'); }));
  await ev(() => window.__sb.setArmour('Gravis'));
  const gl = await marks('legs');
  ck('Gravis: the heavy legs (moved from Tacticus) are listed', Object.keys(gl).join() === 'Gravis' && await ev(() => window.__sb.candidates(window.__sb.SLOT.legs).some(p => p.name === 'Marta Oct 2025 - Heavy Flying Legs')), gl);
  ck('bases are the same for every armour', JSON.stringify(tb) === JSON.stringify(mb) && JSON.stringify(mb) === JSON.stringify(await marks('base')), [tb, mb]);
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
