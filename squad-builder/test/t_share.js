// The shared page (share_server.py): signs in, reads the library over HTTP, hides the folder setup and Hide parts,
// and "Send for printing" lands in _builder/received/<name>/<time>/ as the page's own requests, model ids prefixed with
// the name. node t_share.js URL USER PASS RECEIVED_DIR
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const [URL, USER, PASS, REC] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  let fails = 0; const ck = (l, c, d) => { console.log((c ? '  ok   ' : '  FAIL ') + l + (c ? '' : '  ' + JSON.stringify(d))); if (!c) fails++; };
  const bad = await b.newContext({ httpCredentials: { username: USER, password: 'wrong-password' } });
  const r0 = await (await bad.newPage()).goto(URL); ck('a wrong password is refused', r0.status() === 401, r0.status()); await bad.close();
  const ctx = await b.newContext({ httpCredentials: { username: USER, password: PASS }, viewport: { width: 1500, height: 900 } });
  const page = await ctx.newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL);
  await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
  ck('signed in: the page reads the library over HTTP', page.url().includes('share=1'), page.url());
  const ui = await page.evaluate(() => ({ setup: document.getElementById('setupbtn').hidden, hid: document.getElementById('showhid').closest('label').hidden,
    inb: document.getElementById('inbtxt').textContent }));
  ck('no folder setup, no Hide parts, says where Send goes', ui.setup && ui.hid && /printing/.test(ui.inb), ui);
  const ev = (f, a) => page.evaluate(f, a);
  const pick = async (slot, n) => { await ev((s) => window.__sb.goSlot(s), slot); const i = await ev((n) => window.__sb.S.parts.find(p => p.name === n).id, n); await ev((i) => window.__sb.choose(i), i); await page.waitForTimeout(150); };
  await pick('torso', 'MarFil Assault - Torso 1'); await pick('legs', 'MarFil Intercessor - Legs 1');
  await pick('plateR', 'MarFil Assault - Hip Plate L'); await pick('plateL', 'MarFil Assault - Hip Plate L'); await pick('buckle', 'MarFil Assault - Buckle');
  const want = await ev(() => window.__sb.requestsFor());
  ck('the Send button says printing', /printing/.test(await page.textContent('#sendbtn')), await page.textContent('#sendbtn'));
  const before = fs.existsSync(path.join(REC, USER)) ? fs.readdirSync(path.join(REC, USER)).length : 0;
  await page.click('#sendbtn'); await page.waitForFunction(() => /Sent|Couldn't/.test(document.getElementById('status').textContent), null, { timeout: 15000 });
  const st = await page.textContent('#status'); ck('sent', /^Sent 5 parts for 1 model/.test(st), st);
  const sets = fs.readdirSync(path.join(REC, USER)).sort(); ck('one new received set', sets.length === before + 1, sets);
  const dir = path.join(REC, USER, sets[sets.length - 1]); const got = fs.readdirSync(dir).sort().map(f => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
  ck('every part saved, in order', got.length === want.length && got.every((g, i) => g.path === want[i].path && g.category === want[i].category && (g.socket || '') === (want[i].socket || '')), got.map(g => g.name));
  ck('model id carries the name', got.every(g => g.model === got[0].model) && /^squad-\d+-1$/.test(got[0].model.slice(USER.length + 1)) && got[0].model.startsWith(USER + '-'), got.map(g => g.model));
  ck('the torso keeps its place', JSON.stringify(got[0].at) === JSON.stringify(want[0].at), [got[0].at, want[0].at]);
  ck('no page errors', !errs.length, errs);
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
