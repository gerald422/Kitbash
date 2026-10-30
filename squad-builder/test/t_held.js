// Weapons: the toothed chainswords in either hand (left = the mirrored copy), and a weapon held in both hands
// (Two-Handed Held) in the right hand, which takes the left hand's slot too.
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8777/Squad%20Builder.html?lib=/reallib/&libpath=D%3A%5CKitbash%20Library';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL);
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  let fails = 0; const ck = (l, c, d) => { console.log((c ? '  ok   ' : '  FAIL ') + l + (c ? '' : '  ' + JSON.stringify(d))); if (!c) fails++; };
  const ev = (f, a) => page.evaluate(f, a);
  await ev(() => { const sb = window.__sb, id = (n) => ({id: sb.S.parts.find(p => p.name === n).id});
    sb.S.models = [{torso: id('MarFil Assault - Torso 3'), legs: id('MarFil Assault - Legs 1A'), armR: id('MarFil Assault - Arm 1A R'), armL: id('MarFil Assault - Arm 1B L')}]; sb.goSlot('handR'); });
  const names = (k) => ev((k) => { const sb = window.__sb; return sb.candidates(sb.SLOT[k]).map(p => [p.name, sb.asFor(p, sb.SLOT[k]).name]); }, k);
  const r = await names('handR'), l = await names('handL');
  ck('right hand: chainswords, glaives and the two-handed glaives', r.filter(x => /Toothed - Chainsword/.test(x[0])).length === 12 && r.filter(x => /Chainglaive \d/.test(x[0])).length === 12 && r.filter(x => /Two Hands/.test(x[0])).length === 12, r.length);
  ck('left hand: the mirrored chainswords and glaives, no two-handed', l.filter(x => /\(left hand\)/.test(x[1])).length === 24 && !l.some(x => /Two Hands/.test(x[0])), l.slice(0, 3));
  await ev(() => { const sb = window.__sb; sb.choose(sb.S.parts.find(p => p.name === 'Bits Toothed - Chainsword 01').id); sb.goSlot('handL'); sb.choose(sb.S.parts.find(p => p.name === 'Bits Toothed - Chainsword 07').id); });
  let L = await ev(() => window.__sb.layout(0).filter(x => /hand/.test(x.slot)).map(x => [x.slot, !!x.W, x.as.name]));
  ck('a chainsword in each hand, the left one the mirrored copy', L.length === 2 && L.every(x => x[1]) && /left hand/.test(L[1][2]), L);
  await ev(() => { const sb = window.__sb; sb.goSlot('handR'); sb.choose(sb.S.parts.find(p => p.name === 'Bits Toothed - Chainglaive Two Hands 01').id); });
  L = await ev(() => window.__sb.layout(0).filter(x => /hand/.test(x.slot)).map(x => [x.slot, !!x.W, x.note]));
  ck('a two-handed glaive takes the left hand too', L.find(x => x[0] === 'handR')[1] && /two-handed weapon/.test(L.find(x => x[0] === 'handL')[2]), L);
  const reqs = await ev(() => window.__sb.requestsFor().filter(r => /Toothed/.test(r.name)).map(r => [r.category, r.socket]));
  ck('only the glaive is sent, on Hand R', reqs.length === 1 && reqs[0][0] === 'Two-Handed Held' && reqs[0][1] === 'Hand R', reqs);
  ck('Next skips the left hand', await ev(() => window.__sb.skippable('handL')), null);
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
