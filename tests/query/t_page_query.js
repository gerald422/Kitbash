// Josh's query.blend model on the page, old index vs corrected index: each part relative to the torso, against Josh's placement.
const { chromium } = require('playwright');
const fs = require('fs');
const PM = JSON.parse(fs.readFileSync('/home/claude/twoarm/query/pagemodel.json'));
function rel(A, B) {            // inverse(A) * B for row-major 4x4 arrays, rigid (scale removed)
  const n = (M) => { const R = [0, 1, 2].map(c => Math.hypot(M[0][c], M[1][c], M[2][c])); return M.map((r, i) => i < 3 ? [r[0] / R[0], r[1] / R[1], r[2] / R[2], r[3]] : r); };
  A = n(A); B = n(B);
  const Rt = [0, 1, 2].map(i => [0, 1, 2].map(j => A[j][i]));
  const t = [0, 1, 2].map(i => -(Rt[i][0] * A[0][3] + Rt[i][1] * A[1][3] + Rt[i][2] * A[2][3]));
  const Ai = [[...Rt[0], t[0]], [...Rt[1], t[1]], [...Rt[2], t[2]], [0, 0, 0, 1]];
  return Ai.map(r => [0, 1, 2, 3].map(j => r.reduce((s, x, k) => s + x * B[k][j], 0)));
}
function diff(P, Q) {           // P, Q relative matrices: mm and degrees between them
  const D = rel(P, Q);
  const tr = D[0][0] + D[1][1] + D[2][2];
  return [Math.hypot(D[0][3], D[1][3], D[2][3]), Math.acos(Math.max(-1, Math.min(1, (tr - 1) / 2))) * 180 / Math.PI];
}
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  let fails = 0;
  for (const lib of ['qlibold', 'qlib']) {
    const page = await b.newPage({ viewport: { width: 1400, height: 900 } });
    page.on('pageerror', e => { console.log('ERR', e.message); fails++; });
    await page.goto(`http://localhost:8777/Squad%20Builder.html?lib=/${lib}/`);
    await page.waitForFunction(() => window.__sb && window.__sb.S.parts.length > 0, null, { timeout: 60000 });
    const out = await page.evaluate((m) => {
      const sb = window.__sb; sb.S.models = [JSON.parse(JSON.stringify(m))];
      const res = {};
      sb.layout(0).forEach(x => { if (x.W) res[x.slot] = [0, 1, 2, 3].map(r => [0, 1, 2, 3].map(c => x.W.elements[c * 4 + r])); });
      return res;
    }, PM.model);
    await page.waitForTimeout(500);
    const torsoP = out.torso, torsoQ = PM.Q.torso.M;
    console.log(`== ${lib === 'qlib' ? 'corrected index' : 'index before'}`);
    for (const k of Object.keys(PM.Q)) {
      if (k === 'torso') continue;
      if (!out[k]) { console.log(`  ${k}: not placed`); continue; }
      const [mm, deg] = diff(rel(torsoP, out[k]), rel(torsoQ, PM.Q[k].M));
      const want = lib === 'qlib' && !['head', 'beltF'].includes(k);
      const ok = !want || (mm < 0.05 && deg < 0.1);
      if (!ok) fails++;
      console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${k.padEnd(6)} ${PM.Q[k].name.slice(0, 44).padEnd(44)} ${mm.toFixed(2).padStart(6)} mm ${deg.toFixed(1).padStart(5)} deg`);
    }
    await page.close();
  }
  await b.close();
  console.log('fails:', fails);
})();
