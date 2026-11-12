// The shared page: the owner's Save fit goes to the PC through share_server.py; anyone else's lasts the visit.
//   node t_share_adjust.js URL OWNER OWNERPASS FRIEND FRIENDPASS      (run by t_share_correct.py)
const { chromium } = require('playwright');
const [URL, OU, OP, FU, FP] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  let fails = 0; const ck = (l, c, d) => { console.log((c ? '  ok   ' : '  FAIL ') + l + (c ? '' : '  ' + JSON.stringify(d))); if (!c) fails++; };
  for (const [user, pass, owner] of [[FU, FP, false], [OU, OP, true]]) {
    const ctx = await b.newContext({ httpCredentials: { username: user, password: pass }, viewport: { width: 1500, height: 900 } });
    const page = await ctx.newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message));
    await page.goto(URL); await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
    await page.evaluate(() => { const S = window.__sb.S, id = n => ({ id: S.parts.find(p => p.name === n).id });
      S.models = [{ legs: id('MarFil Assault - Legs 1A'), torso: id('MarFil Assault - Torso 1'), armR: id('MarFil Assault - Arm 1B R'), handR: id('MarFil Assault - Chain Sword 1 R') }]; window.__sb.goSlot('legs'); });
    await page.waitForFunction(() => window.__sb.adj.meshes().length >= 4, null, { timeout: 30000 });
    await page.click('#adjbtn');
    await page.evaluate(() => { window.__sb.adj.select(0, 'handR'); const p = window.__sb.adj.pivot(); p.rotateY(7 * Math.PI / 180); window.__sb.adj.changed(); });
    await page.click('#adjsave'); await page.waitForFunction(() => /Saved|Couldn/.test(document.getElementById('status').textContent), null, { timeout: 10000 });
    const st = await page.textContent('#status');
    ck(owner ? 'the owner: Save fit is written on the PC' : "someone else: Save fit lasts the visit, with the reason", owner ? /saved to the library on the PC/.test(st) : /this visit only: saving fits needs the owner/.test(st), st);
    ck('no page errors', errs.length === 0, errs); await ctx.close();
  }
  await b.close(); process.exit(fails ? 1 : 0);
})();
