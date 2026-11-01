/* Squad Builder: pick a torso, then legs, arms, head... for one model or a whole
   squad, see each part where it will go, and send the lot to Blender (TIOW Inbox).
   Parts are placed with the same maths as Part Sockets: socket @ gap @ fit. */
(function () {
  "use strict";
  var THREE = window.THREE;

  // ------------------------------------------------------------------ joints (TIOW Inbox's table)
  var JOINTS = {
    "Arms": {socket: "Shoulder", sided: true},
    "Two-Handed Guns": {socket: "Shoulder R", spans: ["Shoulder L"]},
    "Two-Handed Melee": {socket: "Shoulder R", spans: ["Shoulder L"]},
    "Heavy Weapons": {socket: "Shoulder R", spans: ["Shoulder L"]},
    "Two-Handed Held": {socket: "Hand R"},     // held in both hands, no arms of its own: right hand, the other hand meets the left arm
    "Pistols": {socket: "Hand", sided: true}, "Melee": {socket: "Hand", sided: true},
    "Shields": {socket: "Hand", sided: true}, "Hands": {socket: "Hand", sided: true},
    "Heads": {socket: "Neck"}, "Backpacks": {socket: "Back"}, "Jump Packs": {socket: "Back"},
    "Legs": {socket: ["Waist", "Flat Waist"]}, "Adapters": {socket: "Waist"}, "Bases": {socket: "Base"},
    "Shoulder Pads": {socket: "Pad", sided: true, mirrorLeft: true},
    "Knee Pads": {socket: "Shin", sided: true, mirrorLeft: true},
    "Loincloths": {socket: "Belt Front"},
    // blade wings bring their connector (the wing's "adaptor") onto the pack's Wing Mount and hang from it (TIOW Inbox 1.17.5)
    "Wings": {socket: "Wing", sided: true, adaptor: {"Wing R": "Wing Mount R", "Wing L": "Wing Mount L"}},
    "Wing Mounts": {socket: "Wing Mount", sided: true}
  };
  var ALIAS = {"arm__Torso_r": "Shoulder R", "arm__Torso_l": "Shoulder L", "Wrist_socket_r": "Hand R",
    "Wrist_socket_l": "Hand L", "Head": "Neck", "Backpack": "Back"};
  function canon(t) { return ALIAS[t] || t; }

  // the steps, their slots, and where each slot goes: [host slot, socket]
  var STEPS = [
    {key: "base", label: "Base", types: ["Bases"], slots: [{k: "base", host: "legs", sock: "Base"}]},
    {key: "legs", label: "Legs", types: ["Legs"], slots: [{k: "legs"}]},
    {key: "torso", label: "Torso", types: ["Chests"], slots: [{k: "torso"}]},
    {key: "arms", label: "Arms", types: ["Arms", "Two-Handed Guns", "Two-Handed Melee", "Heavy Weapons"],
      slots: [{k: "armR", side: "R", host: "torso", sock: "Shoulder R"}, {k: "armL", side: "L", host: "torso", sock: "Shoulder L"},
              {k: "arm2", tab: "Two-handed", lab: "2H", host: "torso", sock: "Shoulder R"}]},
    {key: "head", label: "Head", types: ["Heads"], slots: [{k: "head", host: "torso", sock: "Neck"}]},
    {key: "pack", label: "Back", types: ["Backpacks", "Jump Packs"], slots: [{k: "pack", host: "torso", sock: "Back"}]},
    {key: "wings", label: "Wings", types: ["Wings"],
      slots: [{k: "wingR", side: "R", host: "pack", sock: "Wing R"}, {k: "wingL", side: "L", host: "pack", sock: "Wing L"}]},
    {key: "pads", label: "Shoulder pads", types: ["Shoulder Pads"],
      slots: [{k: "padR", side: "R", host: "armR", sock: "Pad R"}, {k: "padL", side: "L", host: "armL", sock: "Pad L"}]},
    {key: "weapons", label: "Weapons", types: ["Pistols", "Melee", "Two-Handed Held", "Shields", "Hands"],
      slots: [{k: "handR", side: "R", host: "armR", sock: "Hand R"}, {k: "handL", side: "L", host: "armL", sock: "Hand L"}]},
    {key: "shins", label: "Shin pads", types: ["Knee Pads"],
      slots: [{k: "shinR", side: "R", host: "legs", sock: "Shin R"}, {k: "shinL", side: "L", host: "legs", sock: "Shin L"}]},
    // the front of the belt is the loincloth's alone (Josh, Oct 30); belt bits go on the hips and the back
    {key: "loin", label: "Loincloth", types: ["Loincloths"], slots: [{k: "loin", host: "legs", sock: "Belt Front"}]},
    {key: "belt", label: "Belt", types: ["Accessories", "Grenades", "Seals", "Trophies"], byFit: true,
      slots: [{k: "hipR", tab: "Right hip", lab: "R", host: "legs", sock: "Hip R"}, {k: "hipL", tab: "Left hip", lab: "L", host: "legs", sock: "Hip L"},
              {k: "beltB", tab: "Back", lab: "B", host: "legs", sock: "Belt Back"}]}
  ];
  var SLOT = {};
  STEPS.forEach(function (st, i) { st.slots.forEach(function (sl) { sl.step = i; SLOT[sl.k] = sl; }); });
  var ORDER = ["torso", "legs", "arm2", "armR", "armL", "head", "pack", "wingR", "wingL", "padR", "padL", "handR", "handL", "shinR", "shinL", "loin", "hipR", "hipL", "beltB", "base"];   // how a model hangs together (and is sent)
  var PICK = ["base", "legs", "torso", "armR", "armL", "arm2", "head", "pack", "wingR", "wingL", "padR", "padL", "handR", "handL", "shinR", "shinL", "loin", "hipR", "hipL", "beltB"];   // the order you pick in
  // a two-handed piece (both arms and the weapon in one) takes both shoulders: these slots can't be filled with it
  // TIOW Inbox finds pad and wrist spots on single arms only, so a two-handed piece takes a pad only where one was saved by hand
  var COVERED = {padR: "no pad spot on the two-handed piece", padL: "no pad spot on the two-handed piece",
    handR: "built into the two-handed piece", handL: "built into the two-handed piece"};
  var COVERED_NOTE = {padR: "Two-handed pieces have no pad spots yet: Blender would leave a pad beside the model, so it isn't sent.",
    handR: "This model's two-handed piece has its weapon built in: no hands to fill."};
  var HELD_NOTE = "The right-hand weapon is held in both hands: its other hand meets the left arm in Blender.";
  COVERED_NOTE.padL = COVERED_NOTE.padR; COVERED_NOTE.handL = COVERED_NOTE.handR;
  function covered(picks, k) {    // why slot k can't be filled on a model with a two-handed piece, or ""
    if (k === "handL" && picks.handR && (S.byId[picks.handR.id] || {}).type === "Two-Handed Held") return "the other hand of the two-handed weapon";
    if (!picks.arm2 || !COVERED[k]) return "";
    var p = S.byId[picks.arm2.id], want = SLOT[k].sock;
    return p && (p.sockets || []).some(function (q) { return q.t === want; }) ? "" : COVERED[k];
  }
  function hostKey(picks, sl) {   // the right pad hangs from the two-handed piece when there is one
    return (sl.host === "armR" || sl.host === "armL") && picks.arm2 ? "arm2" : sl.host;
  }
  var SPACING = 80;              // mm between models in a squad

  // ------------------------------------------------------------------ state
  var S = {
    index: null, parts: [], byId: {}, types: {}, source: null, libHandle: null, inbHandle: null,
    libPath: "D:\\Kitbash Library", adaptor: 3, models: [{}], cur: 0, same: true, step: 0, slot: "base",
    hover: null, geo: {}, geoWait: {}, thumbs: {}, sentLog: [],
    hide: {lines: [], paths: {}, words: [], types: []}, showHidden: false
  };
  var params = new URLSearchParams(location.search);
  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function status(msg) { $("status").textContent = msg || ""; }
  try {
    var lp = localStorage.getItem("sb.libpath"); if (lp) S.libPath = lp;
    var an = +localStorage.getItem("sb.adaptor"); if (an) S.adaptor = an;
  } catch (e) { /* storage blocked: keep the defaults */ }
  if (params.get("libpath")) S.libPath = params.get("libpath");

  // ------------------------------------------------------------------ matrices (sidecars hold 4x4 row by row)
  function M4(a) { var m = new THREE.Matrix4(); m.set.apply(m, a); return m; }
  var MX = M4([-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
  function T(x, y, z) { return new THREE.Matrix4().makeTranslation(x, y, z); }
  function rotOnly(m) { var r = new THREE.Matrix4().extractRotation(m); return r; }
  function conj(a) { return MX.clone().multiply(M4(a)).multiply(MX); }
  function flat(m) { var e = m.clone().transpose().elements; return Array.prototype.slice.call(e); }
  function swapSide(t) {
    if (/ R$/.test(t)) return t.slice(0, -2) + " L";
    if (/ L$/.test(t)) return t.slice(0, -2) + " R";
    if (/_r$/.test(t)) return t.slice(0, -2) + "_l";
    if (/_l$/.test(t)) return t.slice(0, -2) + "_r";
    return t;
  }

  // ------------------------------------------------------------------ reading the library
  function idb() {
    return new Promise(function (res, rej) {
      var r = indexedDB.open("squad-builder", 1);
      r.onupgradeneeded = function () { r.result.createObjectStore("h"); };
      r.onsuccess = function () { res(r.result); }; r.onerror = function () { rej(r.error); };
    });
  }
  function idbGet(k) { return idb().then(function (db) { return new Promise(function (res) { var q = db.transaction("h").objectStore("h").get(k); q.onsuccess = function () { res(q.result); }; q.onerror = function () { res(null); }; }); }).catch(function () { return null; }); }
  function idbSet(k, v) { return idb().then(function (db) { db.transaction("h", "readwrite").objectStore("h").put(v, k); }).catch(function () {}); }

  function readBytes(rel) {
    if (S.source) return fetch(S.source + rel.split("/").map(encodeURIComponent).join("/")).then(function (r) { if (!r.ok) throw new Error(rel + " " + r.status); return r.arrayBuffer(); });
    var parts = rel.split("/"), d = Promise.resolve(S.libHandle);
    parts.slice(0, -1).forEach(function (p) { d = d.then(function (h) { return h.getDirectoryHandle(p); }); });
    return d.then(function (h) { return h.getFileHandle(parts[parts.length - 1]); })
      .then(function (fh) { return fh.getFile(); }).then(function (f) { return f.arrayBuffer(); });
  }
  function BDIR() { return window.SB_DEMO ? "builder/" : "_builder/"; }   // the online demo cannot publish a "_" folder
  function loadIndex() {
    return readBytes(BDIR() + "index.json").then(function (b) {
      var idx = JSON.parse(new TextDecoder().decode(b));
      S.index = idx; S.parts = idx.parts; S.types = idx.types || {}; S.byId = {};
      if (idx.joints) Object.keys(idx.joints).forEach(function (k) { if (JOINTS[k] && idx.joints[k] && typeof idx.joints[k] === "object") Object.assign(JOINTS[k], idx.joints[k]); });
      S.parts.forEach(function (p) { S.byId[p.id] = p; norm(p); (p.variants || []).forEach(norm); });
      return readBytes("_hidden.txt").then(function (b) { readHide(new TextDecoder().decode(b)); }, function () { readHide(""); });
    }).then(function () {
      $("libdot").classList.add("on");
      $("libtxt").textContent = S.parts.length + " parts";
      renderAll();
    });
  }
  function norm(d) {           // socket and fit names on the current names
    var f = {};
    Object.keys(d.fits || {}).forEach(function (k) { f[canon(k)] = d.fits[k]; });
    d.fits = f;
    (d.sockets || []).forEach(function (s) { s.t = canon(s.t); });
  }

  // ------------------------------------------------------------------ preview meshes
  function geometry(id) {
    if (S.geo[id]) return Promise.resolve(S.geo[id]);
    if (S.geoWait[id]) return S.geoWait[id];
    var p = S.byId[id];
    if (!p || !p.prev) return Promise.resolve(null);
    var get;
    if (p.prev.indexOf("#") > 0) {          // a slice of a pack file (the online demo)
      var at = p.prev.split("#"), r = at[1].split(":").map(Number);
      S.packs = S.packs || {};
      S.packs[at[0]] = S.packs[at[0]] || readBytes(BDIR() + at[0]).then(function (b) {
        if (!/\.txt$/.test(at[0])) return b;                // base64 text: the online demo can only serve text
        var t = atob(new TextDecoder().decode(b).replace(/\s+/g, "")), u = new Uint8Array(t.length);
        for (var k = 0; k < t.length; k++) u[k] = t.charCodeAt(k);
        return u.buffer;
      });
      get = S.packs[at[0]].then(function (b) { return b.slice(r[0], r[0] + r[1]); });
    } else get = readBytes(BDIR() + p.prev);
    S.geoWait[id] = get.then(function (b) {
      var dv = new DataView(b), nv = dv.getUint32(4, true), nt = dv.getUint32(8, true);
      var pos = new Float32Array(b, 12, nv * 3), idx = new Uint32Array(b.slice(12 + nv * 12, 12 + nv * 12 + nt * 12));
      var g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
      g.setIndex(new THREE.BufferAttribute(idx, 1));
      g.computeVertexNormals(); g.computeBoundingBox();
      var e = new THREE.EdgesGeometry(g, 32);
      S.geo[id] = {g: g, e: e};
      return S.geo[id];
    }).catch(function () { return null; });
    return S.geoWait[id];
  }

  // ------------------------------------------------------------------ which parts go in a slot, and as what
  function spec(p) { return JOINTS[p.type] || {}; }
  function plainMirror(d) {
    var o = {fits: {}, sockets: [], upright: d.upright};
    Object.keys(d.fits || {}).forEach(function (k) { o.fits[swapSide(k)] = flat(conj(d.fits[k])); });
    (d.sockets || []).forEach(function (s) { o.sockets.push({t: swapSide(s.t), m: flat(conj(s.m))}); });
    return o;
  }
  /* {data, v, mirror, align, name} for this part in this slot, or null if it can't go there */
  function asFor(p, sl) {
    var side = sl.side, sp = spec(p), base = {data: p, v: null, mirror: false, align: null, name: p.name};
    if (STEPS[sl.step].byFit) return p.fits[sl.sock] ? base : null;   // belt bits: wherever they have a fit for
    if (sl.k === "arm2") return sp.spans ? base : null;           // the Two-handed tab: pieces with both arms, on Shoulder R
    if (sp.spans) return null;                                    // ...and nowhere else
    if (!side) return base;
    var mine = p.side || sideOfFits(p);
    // a part with no side of its own is a right-hand part (Mar Fil ship their pads that way)
    if (mine === side || (!mine && (side === "R" || p.fits[(sp.socket || "") + " " + side]))) return base;
    var v = (p.variants || []).filter(function (x) { return x.side === side && !x.synth; })[0];
    if (v) return {data: v, v: v.i, mirror: false, align: M4(v.align), name: v.name};
    if (sp.mirrorLeft || sp.mirrorSides) {
      if (p.fits[sp.socket + " " + side]) return base;
      return {data: plainMirror(p), v: null, mirror: true, align: MX.clone(), name: p.name + " (mirrored)"};
    }
    return null;
  }
  function sideOfFits(p) {
    var s = Object.keys(p.fits || {}).map(function (k) { return (/ ([RL])$/.exec(k) || [])[1]; }).filter(Boolean);
    return s.length && s.every(function (x) { return x === s[0]; }) ? s[0] : null;
  }
  // ------------------------------------------------------------------ parts you've hidden (the library's _hidden.txt)
  // One line each: a part's library path (what the Hide button writes), "word: aquila" (any part with that in its
  // name), "type: Seals" (a whole type), or a "#" comment. Nothing is deleted: the page just leaves these out.
  var HIDE_HEAD = ["# Parts the Squad Builder leaves out. Nothing is deleted: take a line out to bring a part back.",
    "# A library path hides that part (the page's Hide button writes these), \"word: <text>\" hides every part",
    "# with that in its name, \"type: <type>\" a whole type. Renegade chapter: no aquilas, purity seals or scrolls.",
    "word: aquila", "word: aquilla", "word: purity seal", "word: scroll", "type: Seals"];
  function readHide(txt) {
    var lines = txt.replace(/^\ufeff/, "").split(/\r?\n/);
    if (!txt.trim()) lines = HIDE_HEAD.slice();
    var h = {lines: lines, paths: {}, words: [], types: [], fresh: !txt.trim()};
    lines.forEach(function (l) {
      var t = l.trim(), m;
      if (!t || t[0] === "#") return;
      if ((m = /^word:\s*(.+)$/i.exec(t))) h.words.push(m[1].toLowerCase());
      else if ((m = /^type:\s*(.+)$/i.exec(t))) h.types.push(m[1].toLowerCase());
      else h.paths[t.toLowerCase()] = true;
    });
    S.hide = h;
  }
  function hiddenBy(p) {            // why a part is hidden ("" if it isn't)
    if (S.hide.paths[p.path.toLowerCase()]) return "hidden";
    var t = (p.name + " " + (p.orig || "")).toLowerCase(), w;
    for (var i = 0; i < S.hide.words.length; i++) { w = S.hide.words[i]; if (t.indexOf(w) >= 0) return "word: " + w; }
    if (S.hide.types.indexOf(String(p.type).toLowerCase()) >= 0) return "type: " + p.type;
    return "";
  }
  function saveHide() {
    var body = S.hide.lines.join("\r\n").replace(/(\r\n)*$/, "") + "\r\n";
    if (!S.libHandle) return Promise.resolve();          // test or demo: kept for this visit
    return S.libHandle.getFileHandle("_hidden.txt", {create: true}).then(function (fh) { return fh.createWritable(); })
      .then(function (w) { return w.write(body).then(function () { return w.close(); }); })
      .catch(function (e) { status("Couldn't save _hidden.txt in the library: " + e.message); });
  }
  function toggleHide(p) {
    var why = hiddenBy(p);
    if (why && why !== "hidden") { status(p.name + " is hidden by \"" + why + "\" in _hidden.txt: take that line out to bring it back."); return; }
    if (why) S.hide.lines = S.hide.lines.filter(function (l) { return l.trim().toLowerCase() !== p.path.toLowerCase(); });
    else S.hide.lines.push(p.path);
    readHide(S.hide.lines.join("\n"));
    saveHide(); renderPicker(); status(why ? p.name + " is back." : p.name + " hidden: it's left out once Hide parts is off.");
  }
  function candidates(sl, all) {
    var st = STEPS[sl.step];
    return S.parts.filter(function (p) { return st.types.indexOf(p.type) >= 0 && asFor(p, sl) && (all || S.showHidden || !hiddenBy(p)); });
  }

  // ------------------------------------------------------------------ placing a model
  function socketsOf(inst) {
    var out = {};
    (inst.as.data.sockets || []).forEach(function (s) { out[s.t] = inst.W.clone().multiply(M4(s.m)); });
    return out;
  }
  function fitMatrix(as, tname) {
    var f = as.data.fits && as.data.fits[tname];
    if (f) return M4(f);
    var t = S.types[tname];
    return t && t.mat ? M4(t.mat) : null;
  }
  function onto(sockW, as, tname) {
    var off = fitMatrix(as, tname);
    if (!off) return null;
    var gap = (S.types[tname] || {}).gap || 0;
    return sockW.clone().multiply(T(0, 0, gap)).multiply(off);
  }
  function natural(a, b) {
    var x = a.toLowerCase().split(/(\d+)/), y = b.toLowerCase().split(/(\d+)/);
    for (var i = 0; i < Math.min(x.length, y.length); i++) {
      if (x[i] === y[i]) continue;
      var nx = +x[i], ny = +y[i];
      return (i % 2 && !isNaN(nx) && !isNaN(ny)) ? nx - ny : (x[i] < y[i] ? -1 : 1);
    }
    return x.length - y.length;
  }
  function connectorOf(p) {      // the part a wing brings with it (its sockets file's "adaptor": a path in the library)
    var want = String(p.adaptor || "").toLowerCase();
    return want ? S.parts.filter(function (q) { return q.path.toLowerCase() === want; })[0] : null;
  }
  function adaptorPart() {      // the one TIOW Inbox brings: its Adaptor number, in folder order
    var ads = S.parts.filter(function (p) { return p.type === "Adapters"; }).sort(function (a, b) { return natural(a.path.split("\\").pop(), b.path.split("\\").pop()); });
    return ads[Math.min(Math.max(S.adaptor, 1), ads.length) - 1];
  }
  // ------------------------------------------------------------------ a base rises to meet the feet (TIOW Inbox 1.17.2's settle_base)
  var BASE = {cell: 0.5, step: 0.25, band: 1000.0, sink: 0.2, max: 25.0}, riseCache = {};
  function trisIn(g, M) {        // the preview's triangles through M, as flat [x0,y0,z0, x1,..] per triangle
    var a = g.g.attributes.position.array, ix = g.g.index.array, out = new Float64Array(ix.length * 3), v = new THREE.Vector3();
    for (var i = 0; i < ix.length; i++) { v.set(a[ix[i] * 3], a[ix[i] * 3 + 1], a[ix[i] * 3 + 2]).applyMatrix4(M); out[i * 3] = v.x; out[i * 3 + 1] = v.y; out[i * 3 + 2] = v.z; }
    return out;
  }
  function heightField(t, keep, lowest) {    // keep(i) picks triangles; min (lowest) or max z per 0.5 mm cell
    var f = new Map();
    for (var i = 0; i < t.length / 9; i++) {
      if (!keep(i)) continue;
      var o = i * 9, ax = t[o], ay = t[o + 1], az = t[o + 2], bx = t[o + 3], by = t[o + 4], bz = t[o + 5], cx = t[o + 6], cy = t[o + 7], cz = t[o + 8];
      var e = Math.max(Math.hypot(bx - ax, by - ay, bz - az), Math.hypot(cx - bx, cy - by, cz - bz), Math.hypot(ax - cx, ay - cy, az - cz));
      var k = Math.min(60, Math.max(1, Math.ceil(e / BASE.step)));
      for (var p = 0; p <= k; p++) for (var q = 0; q <= k - p; q++) {
        var u = p / k, w = q / k, x = ax + u * (bx - ax) + w * (cx - ax), y = ay + u * (by - ay) + w * (cy - ay), z = az + u * (bz - az) + w * (cz - az);
        var key = Math.floor(x / BASE.cell) * 100003 + Math.floor(y / BASE.cell), old = f.get(key);
        if (old === undefined || (lowest ? z < old : z > old)) f.set(key, z);
      }
    }
    return f;
  }
  function baseRise(legs, base, hs) {
    var key = legs.part.id + "|" + legs.as.v + "|" + legs.as.mirror + "|" + base.part.id;
    if (key in riseCache) return riseCache[key];
    var gl = S.geo[legs.part.id], gb = S.geo[base.part.id];
    if (!gl || !gb) {
      [legs.part.id, base.part.id].forEach(function (id) { if (!S.geo[id]) geometry(id).then(function (g) { if (g) redraw(); }); });
      return 0;
    }
    var inv = hs.clone().invert();
    var ML = inv.clone().multiply(legs.W); if (legs.as.align) ML.multiply(legs.as.align);
    var MB = inv.clone().multiply(base.W); if (base.as.align) MB.multiply(base.as.align);
    var tl = trisIn(gl, ML), tb = trisIn(gb, MB), zl = Infinity, i;
    for (i = 2; i < tl.length; i += 3) if (tl[i] < zl) zl = tl[i];
    var lo = [Infinity, Infinity], hi = [-Infinity, -Infinity];
    function lowTri(j) { var o = j * 9; return Math.min(tl[o + 2], tl[o + 5], tl[o + 8]) < zl + BASE.band; }
    for (i = 0; i < tl.length / 9; i++) if (lowTri(i)) for (var c = 0; c < 3; c++) {
      var x = tl[i * 9 + c * 3], y = tl[i * 9 + c * 3 + 1];
      lo[0] = Math.min(lo[0], x - 1); lo[1] = Math.min(lo[1], y - 1); hi[0] = Math.max(hi[0], x + 1); hi[1] = Math.max(hi[1], y + 1);
    }
    function nearTri(j) {
      var o = j * 9, x0 = Math.min(tb[o], tb[o + 3], tb[o + 6]), x1 = Math.max(tb[o], tb[o + 3], tb[o + 6]);
      var y0 = Math.min(tb[o + 1], tb[o + 4], tb[o + 7]), y1 = Math.max(tb[o + 1], tb[o + 4], tb[o + 7]);
      return x1 >= lo[0] && x0 <= hi[0] && y1 >= lo[1] && y0 <= hi[1];
    }
    var sole = heightField(tl, lowTri, true), top = heightField(tb, nearTri, false), gap = Infinity;
    sole.forEach(function (z, k) { var t = top.get(k); if (t !== undefined && z - t < gap) gap = z - t; });
    var rise = (gap === Infinity || gap <= -BASE.sink || gap > BASE.max) ? 0 : gap + BASE.sink;
    riseCache[key] = rise;
    return rise;
  }

  /* every part of model i placed: [{slot, part, as, W, note}] - with `try` = {slot, part} tried in a slot */
  function layout(i, tryPick) {
    var picks = Object.assign({}, S.models[i] || {});
    if (tryPick) {
      picks[tryPick.slot] = {id: tryPick.part.id};
      if (tryPick.slot === "arm2") { delete picks.armR; delete picks.armL; }        // trying a two-handed piece: it replaces both arms
      else if (tryPick.slot === "armR" || tryPick.slot === "armL") delete picks.arm2;
    }
    var out = [], by = {};
    var at = [-i * SPACING, 0, 0];
    ORDER.forEach(function (k) {
      var pk = picks[k];
      if (!pk) return;
      var p = S.byId[pk.id];
      if (!p) return;
      var sl = SLOT[k], as = asFor(p, sl);
      if (!as) return;
      var inst = {slot: k, part: p, as: as, W: null, note: ""};
      if (k === "torso") {
        var U = as.data.upright ? rotOnly(M4(as.data.upright)) : new THREE.Matrix4();
        inst.W = T(at[0], at[1], at[2]).multiply(U);
      } else if (k === "legs") {
        var torso = by.torso;
        if (!torso) {           // picked before the torso: the legs stand on their own (on the base, if there is one)
          var UL = as.data.upright ? rotOnly(M4(as.data.upright)) : new THREE.Matrix4();
          inst.W = T(at[0], at[1], at[2]).multiply(UL); inst.free = true;
          out.push(inst); by.legs = inst; return;
        }
        var ts = socketsOf(torso), placed = false;
        ["Waist", "Flat Waist"].forEach(function (w) {
          if (!placed && ts[w] && as.data.fits[w]) { inst.W = onto(ts[w], as, w); inst.sock = w; placed = true; }
        });
        if (!placed && as.data.fits["Flat Waist"] && ts["Waist"]) {
          var ad = adaptorPart();
          if (ad) {
            var aas = {data: ad, v: null, mirror: false, align: null, name: ad.name};
            var aw = onto(ts["Waist"], aas, "Waist");
            if (aw) {
              var ainst = {slot: "adaptor", part: ad, as: aas, W: aw, note: "adaptor, brought by the legs"};
              out.push(ainst); by.adaptor = ainst;
              var as2 = socketsOf(ainst);
              if (as2["Flat Waist"]) { inst.W = onto(as2["Flat Waist"], as, "Flat Waist"); placed = !!inst.W; }
            }
          }
        }
        if (!inst.W) inst.note = "no waist fit yet: placed by eye in Blender";
      } else {
        if (covered(picks, k)) { inst.note = covered(picks, k); inst.covered = true; out.push(inst); return; }
        var hk = hostKey(picks, sl), host = by[hk];
        if (!host && k === "base") {      // picked first: the base on its own, on the grid
          inst.W = onto(T(at[0], at[1], at[2]), as, "Base") || T(at[0], at[1], at[2]); inst.free = true;
          out.push(inst); by.base = inst; return;
        }
        if (!host) { inst.note = "needs " + (SLOT[hk] ? STEPS[SLOT[hk].step].label.toLowerCase() : hk); out.push(inst); return; }
        var sock = sl.sock;
        if (spec(p).spans) sock = "Shoulder R";
        var hs = socketsOf(host)[sock];
        var via = (spec(p).adaptor || {})[sock];
        if (!hs && via) {               // a wing: its connector goes on the pack's Wing Mount first, the wing on the connector
          var vs = socketsOf(host)[via], conn = connectorOf(p);
          if (!vs || !conn) { inst.note = !vs ? "no " + via + " on this back" : "its connector isn't in the library"; out.push(inst); return; }
          var cas = asFor(conn, sl);
          var cw = cas && onto(vs, cas, via);
          if (cw) {
            var cinst = {slot: "mount" + (sl.side || ""), part: conn, as: cas, W: cw, note: "connector, brought by the wing"};
            out.push(cinst); by[cinst.slot] = cinst;
            hs = socketsOf(cinst)[sock];
          }
        }
        if (!hs) {
          inst.note = host.part.anchored ? "no " + sock + " on these " + STEPS[SLOT[hk].step].label.toLowerCase() : "Blender finds the " + sock + " socket";
          out.push(inst); return;
        }
        inst.W = onto(hs, as, sock);
        if (!inst.W) inst.note = "no " + sock + " fit yet: placed by eye in Blender";
        else if (k === "base" && (as.data.exact || []).indexOf("Base") < 0) {   // rise to meet the feet, as the inbox does (not once corrected by hand)
          var rise = baseRise(host, inst, hs);
          if (rise) { var zax = new THREE.Vector3().setFromMatrixColumn(hs, 2).normalize().multiplyScalar(rise); inst.W = T(zax.x, zax.y, zax.z).multiply(inst.W); }
        }
        if (spec(p).spans) inst.spans = true;
      }
      out.push(inst);
      if (inst.W) by[k] = inst;
    });
    // stand on the base, as the inbox does
    var legs = by.legs, base = by.base;
    if (legs && base) {
      var bsock = socketsOf(legs)["Base"];
      if (bsock) {
        var up = new THREE.Vector3().setFromMatrixColumn(bsock, 2).normalize();
        var pp = new THREE.Vector3().setFromMatrixPosition(bsock);
        var q = new THREE.Quaternion().setFromUnitVectors(up, new THREE.Vector3(0, 0, 1));
        var turn = T(pp.x, pp.y, pp.z).multiply(new THREE.Matrix4().makeRotationFromQuaternion(q)).multiply(T(-pp.x, -pp.y, -pp.z));
        out.forEach(function (o) { if (o.W) o.W = turn.clone().multiply(o.W); });
        var low = new THREE.Vector3().setFromMatrixPosition(turn.clone().multiply(bsock)).z;
        var g = S.geo[base.part.id];
        if (g) {
          var M = base.W.clone(); if (base.as.align) M.multiply(base.as.align);
          var a = g.g.attributes.position.array, v = new THREE.Vector3();
          for (var j = 0; j < a.length; j += 3) { v.set(a[j], a[j + 1], a[j + 2]).applyMatrix4(M); if (v.z < low) low = v.z; }
        } else if (!S.geoWait[base.part.id]) {
          geometry(base.part.id).then(function (g) { if (g) redraw(); });
        }
        var drop = by.torso ? T(0, 0, -low) : T(at[0] - pp.x, at[1] - pp.y, -low);   // no torso yet: the legs stand on the model's spot
        out.forEach(function (o) { if (o.W) o.W = drop.clone().multiply(o.W); });
      }
    } else if (base && base.free) {
      var gb = S.geo[base.part.id];
      if (gb) {
        var Mb = base.W.clone(); if (base.as.align) Mb.multiply(base.as.align);
        var ab = gb.g.attributes.position.array, vb = new THREE.Vector3(), lowb = Infinity;
        for (var jb = 0; jb < ab.length; jb += 3) { vb.set(ab[jb], ab[jb + 1], ab[jb + 2]).applyMatrix4(Mb); if (vb.z < lowb) lowb = vb.z; }
        base.W = T(0, 0, -lowb).multiply(base.W);
      } else if (!S.geoWait[base.part.id]) geometry(base.part.id).then(function (g) { if (g) redraw(); });
    }
    return out;
  }

  // ------------------------------------------------------------------ the 3D view
  var view = $("view"), renderer, scene, camera, controls, groups = {model: new THREE.Group(), ghost: new THREE.Group()};
  var MAT = {
    part: new THREE.MeshStandardMaterial({color: 0xb9bcb6, roughness: 0.75, metalness: 0.05, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1}),
    cur: new THREE.MeshStandardMaterial({color: 0xd6cdb8, roughness: 0.7, metalness: 0.05, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1}),
    edge: new THREE.LineBasicMaterial({color: 0x23262a, transparent: true, opacity: 0.55}),
    ghost: new THREE.MeshBasicMaterial({color: 0x5fb4ff, transparent: true, opacity: 0.18, depthWrite: false}),
    gedge: new THREE.LineBasicMaterial({color: 0x5fb4ff, transparent: true, opacity: 0.95, depthTest: false})
  };
  function initView() {
    renderer = new THREE.WebGLRenderer({antialias: true});
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    renderer.setClearColor(0x15181b);
    view.insertBefore(renderer.domElement, view.firstChild);
    scene = new THREE.Scene();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x30343a, 0.85));
    var d = new THREE.DirectionalLight(0xffffff, 0.75); d.position.set(60, 120, 160); scene.add(d);
    var grid = new THREE.GridHelper(400, 40, 0x2b3036, 0x22262b); grid.rotation.x = Math.PI / 2; scene.add(grid);
    scene.add(groups.model); scene.add(groups.ghost);
    camera = new THREE.PerspectiveCamera(32, 1, 1, 5000);
    camera.up.set(0, 0, 1);
    camera.position.set(40, 260, 90);
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, 30); controls.enableDamping = true;
    function size() {
      var r = view.getBoundingClientRect();
      renderer.setSize(r.width, r.height, false); camera.aspect = r.width / Math.max(1, r.height); camera.updateProjectionMatrix();
    }
    window.addEventListener("resize", size); size();
    (function loop() { controls.update(); renderer.render(scene, camera); requestAnimationFrame(loop); })();
  }
  function meshFor(inst, ghost, current) {
    var g = S.geo[inst.part.id];
    if (!g) { geometry(inst.part.id).then(function (gg) { if (gg) redraw(); }); return null; }   // no preview: draw nothing, don't loop
    var M = inst.W.clone(); if (inst.as.align) M.multiply(inst.as.align);
    var obj = new THREE.Group();
    var m = new THREE.Mesh(g.g, ghost ? MAT.ghost : current ? MAT.cur : MAT.part);
    var e = new THREE.LineSegments(g.e, ghost ? MAT.gedge : MAT.edge);
    if (ghost) { m.renderOrder = 2; e.renderOrder = 3; }
    [m, e].forEach(function (o) { o.matrixAutoUpdate = false; o.matrix.copy(M); obj.add(o); });
    return obj;
  }
  function clear(g) { while (g.children.length) g.remove(g.children[0]); }
  var framed = 0;
  function redraw() {
    if (!scene) return;
    clear(groups.model); clear(groups.ghost);
    var box = new THREE.Box3();
    S.models.forEach(function (_m, i) {
      layout(i).forEach(function (inst) {
        if (!inst.W) return;
        var o = meshFor(inst, false, i === S.cur && S.models.length > 1);
        if (o) { groups.model.add(o); box.expandByObject(o); }
      });
    });
    if (S.hover) {
      var targets = S.same ? S.models.map(function (_m, i) { return i; }) : [S.cur];
      targets.forEach(function (i) {
        layout(i, S.hover).forEach(function (inst) {
          if (inst.slot !== S.hover.slot || !inst.W) return;
          var o = meshFor(inst, true);
          if (o) groups.ghost.add(o);
        });
      });
    }
    // frame the squad when a model starts or the squad size changes
    var started = S.models.filter(function (m) { return m.torso; }).length;
    if (started !== framed && !box.isEmpty()) {
      framed = started;
      var c = box.getCenter(new THREE.Vector3()), sz = box.getSize(new THREE.Vector3());
      var fov = camera.fov * Math.PI / 180, w = Math.max(sz.x / Math.max(camera.aspect, 0.3), sz.z, 40);
      var dist = w / (2 * Math.tan(fov / 2)) * 1.25 + sz.y / 2;
      controls.target.copy(c); camera.position.set(c.x - dist * 0.25, c.y + dist, c.z + dist * 0.28);
    }
  }

  // ------------------------------------------------------------------ outline drawings for the cards
  var thumbR = null, thumbQ = [], thumbBusy = false;
  function thumb(id, img) {
    if (S.thumbs[id]) { img.src = S.thumbs[id]; return; }
    thumbQ.push([id, img]); pump();
  }
  function pump() {
    if (thumbBusy || !thumbQ.length) return;
    thumbBusy = true;
    var job = thumbQ.shift();
    if (!job[1].isConnected) { thumbBusy = false; return pump(); }
    geometry(job[0]).then(function (g) {
      if (g) S.thumbs[job[0]] = drawThumb(S.byId[job[0]], g);
      if (S.thumbs[job[0]]) job[1].src = S.thumbs[job[0]]; else job[1].replaceWith(Object.assign(document.createElement("span"), {textContent: "no preview", className: "tag"}));
      thumbBusy = false; pump();
    });
  }
  function drawThumb(p, g) {
    if (!thumbR) {
      thumbR = new THREE.WebGLRenderer({antialias: true, preserveDrawingBuffer: true, alpha: true});
      thumbR.setSize(200, 200, false); thumbR.setClearColor(0x000000, 0);
    }
    var sc = new THREE.Scene();
    var U = p.upright ? rotOnly(M4(p.upright)) : new THREE.Matrix4();
    var fill = new THREE.Mesh(g.g, new THREE.MeshBasicMaterial({color: 0x1d2024, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1}));
    var lines = new THREE.LineSegments(g.e, new THREE.LineBasicMaterial({color: 0xd9dcd6}));
    [fill, lines].forEach(function (o) { o.matrixAutoUpdate = false; o.matrix.copy(U); sc.add(o); });
    var b = g.g.boundingBox.clone().applyMatrix4(U), c = b.getCenter(new THREE.Vector3()), s = b.getSize(new THREE.Vector3());
    var half = Math.max(s.x, s.z) * 0.56 + 0.5;
    var cam = new THREE.OrthographicCamera(-half, half, half, -half, 0.1, 2000);
    cam.up.set(0, 0, 1); cam.position.set(c.x - s.length() * 0.35, c.y + 500, c.z + s.length() * 0.2); cam.lookAt(c);
    thumbR.render(sc, cam);
    return thumbR.domElement.toDataURL("image/png");
  }

  // ------------------------------------------------------------------ the panels
  function pickOf(i, k) { return (S.models[i] || {})[k]; }
  function renderSteps() {
    var m = S.cur, html = "", mdl = S.models[m] || {};
    STEPS.forEach(function (st, si) {
      var slots = st.slots.filter(function (sl) {      // arms: the two-handed piece, or the right and left arms
        return st.key !== "arms" || (mdl.arm2 ? sl.k === "arm2" : sl.k !== "arm2");
      });
      var lines = slots.map(function (sl) {
        var pk = pickOf(m, sl.k), p = pk && S.byId[pk.id], txt = "—", flag = false;
        if (covered(mdl, sl.k)) txt = covered(mdl, sl.k);
        else if (p) {
          var as = asFor(p, sl); txt = as ? as.name : p.name;
          var inst = layout(m).filter(function (x) { return x.slot === sl.k; })[0];
          if (inst && !inst.W) { flag = true; txt += " · " + inst.note; }
        }
        var lab = sl.side || sl.lab;
        return '<div class="s' + (flag ? " flag" : "") + '">' + (lab ? '<span class="lab">' + lab + "</span>" : "") + "<b>" + esc(txt) + "</b></div>";
      }).join("");
      html += '<div class="step' + (si === S.step ? " on" : "") + '" data-i="' + si + '" tabindex="0"><div class="t">' + (si + 1) + ". " + esc(st.label) + "</div>" + lines + "</div>";
    });
    $("steps").innerHTML = html;
  }
  function renderModels() {
    if (S.models.length < 2) { $("models").innerHTML = ""; return; }
    var h = S.models.map(function (_m, i) { return '<button class="mtab' + (i === S.cur ? " on" : "") + '" data-m="' + i + '">Model ' + (i + 1) + "</button>"; }).join("");
    h += '<label class="same"><input type="checkbox" id="samechk"' + (S.same ? " checked" : "") + '> Same part for every model</label>';
    $("models").innerHTML = h;
  }
  function uniq(a) { return a.filter(function (v, i) { return v && a.indexOf(v) === i; }).sort(); }
  function renderPicker() {
    var st = STEPS[S.step], sl = SLOT[S.slot];
    $("ptitle").textContent = st.label;
    $("slotseg").innerHTML = st.slots.length > 1 ? st.slots.map(function (x) {
      return '<button data-s="' + x.k + '" class="' + (x.k === S.slot ? "on" : "") + '">' + (x.tab || (x.side === "R" ? "Right" : "Left")) + "</button>";
    }).join("") : "";
    var all = candidates(sl), nhid = candidates(sl, true).length - candidates(sl).length;
    if (S.showHidden) nhid = candidates(sl, true).filter(function (p) { return hiddenBy(p); }).length;
    var mk = $("fmaker").value, kt = $("fkit").value, q = $("fq").value.trim().toLowerCase();
    var makers = uniq(all.map(function (p) { return p.maker; }));
    if (makers.indexOf(mk) < 0) mk = "";          // a maker with nothing in this step: show everything
    $("fmaker").innerHTML = '<option value="">All makers</option>' + makers.map(function (x) { return '<option' + (x === mk ? " selected" : "") + ">" + esc(x) + "</option>"; }).join("");
    var kits = uniq(all.filter(function (p) { return !mk || p.maker === mk; }).map(function (p) { return p.kit; }));
    if (kits.indexOf(kt) < 0) kt = "";
    $("fkit").innerHTML = '<option value="">All kits</option>' + kits.map(function (x) { return '<option' + (x === kt ? " selected" : "") + ">" + esc(x) + "</option>"; }).join("");
    var list = all.filter(function (p) {
      return (!mk || p.maker === mk) && (!kt || p.kit === kt) && (!q || (p.name + " " + p.orig).toLowerCase().indexOf(q) >= 0);
    });
    var mdl = S.models[S.cur] || {}, hk = hostKey(mdl, sl);
    var host = hk && layout(S.cur).filter(function (x) { return x.slot === hk; })[0];
    var note = "";
    if (sl.k === "base") note = pickOf(S.cur, "legs") ? "" : "The legs you pick next stand on it.";
    else if (covered(mdl, sl.k)) note = /two-handed weapon$/.test(covered(mdl, sl.k)) ? HELD_NOTE : COVERED_NOTE[sl.k];
    else if (sl.k === "arm2" && (mdl.armR || mdl.armL)) note = "A two-handed piece has both arms and its weapon: picking one replaces the arms.";
    else if ((sl.k === "armR" || sl.k === "armL") && mdl.arm2) note = "Picking an arm replaces the two-handed piece.";
    else if (hk && !pickOf(S.cur, hk)) note = "Pick " + STEPS[SLOT[hk].step].label.toLowerCase() + " first to see these in place.";
    else if (st.key === "wings") note = host && host.W && socketsOf(host)[JOINTS.Wings.adaptor[sl.sock]]
      ? "Each wing brings its connector onto the pack's " + JOINTS.Wings.adaptor[sl.sock] + " and hangs from it."
      : "This back has no " + JOINTS.Wings.adaptor[sl.sock] + ": only packs with wing mounts take wings.";
    else if (host && host.W && sl.sock && !socketsOf(host)[sl.sock] && !spec({type: st.types[0]}).spans)
      note = host.part.anchored ? "These " + STEPS[SLOT[hk].step].label.toLowerCase() + " have no " + sl.sock + ": Blender will leave the part beside the model for you to place."
                                : "No " + sl.sock + " saved for these " + STEPS[SLOT[hk].step].label.toLowerCase() + " yet: Blender will find it.";
    $("pnote").textContent = note;
    $("pcount").textContent = list.length + " of " + all.length + (nhid ? " · " + nhid + " hidden" : "");
    $("showhid").checked = S.showHidden;
    var chosen = pickOf(S.cur, S.slot);
    var html = list.slice(0, 400).map(function (p) {
      var as = asFor(p, sl);
      var tag = as.v != null ? (as.data.mirror ? "mirrored" : "maker's left copy") : as.mirror ? "mirrored" : sl.k === "arm2" ? p.kit + " · " + p.type.replace("Two-Handed ", "") : p.type === st.types[0] ? p.kit : p.type;
      var fitName = spec(p).spans ? "Shoulder R" : sl.sock;
      var nofit = sl.k === "legs" ? !(as.data.fits["Waist"] || as.data.fits["Flat Waist"]) : fitName ? !fitMatrix(as, fitName) : false;
      if (nofit) tag = "no fit yet";
      var hid = hiddenBy(p);
      return '<div class="card' + (chosen && chosen.id === p.id ? " on" : "") + (hid ? " hid" : "") + '" tabindex="0" data-id="' + p.id + '" title="' + esc(p.path) + '">' +
        (S.showHidden ? '<button class="hide" data-hide="' + p.id + '" title="' + (hid ? (hid === "hidden" ? "Bring this part back" : esc("Hidden by " + hid + " in _hidden.txt")) : "Leave this part out of the builder (nothing is deleted)") + '">' + (hid ? "Unhide" : "Hide") + "</button>" : "") +
        '<div class="img">' + (p.prev ? '<img alt="" data-t="' + p.id + '">' : '<span class="tag">no preview</span>') + "</div>" +
        '<div class="nm">' + esc(as.name.replace(/^[^-]+ - /, "")) + '</div><div class="tag' + (nofit ? " flag" : "") + '">' + esc(tag) + "</div></div>";
    }).join("");
    if (!list.length) html = '<div class="empty">No parts here' + (all.length ? " match the filters." : " fit this slot.") + "</div>";
    if (list.length > 400) html += '<div class="empty">Showing 400 of ' + list.length + ": narrow it with the filters.</div>";
    $("cards").innerHTML = html;
    thumbQ = [];
    observe();
  }
  var io = null;
  function observe() {
    if (!io) io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { io.unobserve(e.target); thumb(e.target.getAttribute("data-t"), e.target); } });
    }, {root: $("cards"), rootMargin: "200px"});
    document.querySelectorAll("#cards img[data-t]").forEach(function (im) { io.observe(im); });
  }
  function renderAll() { renderSteps(); renderModels(); renderPicker(); redraw(); updateSend(); }
  function updateSend() {
    var n = S.models.filter(function (m) { return m.torso; }).length;
    $("sendbtn").disabled = !n;
    $("sendbtn").textContent = n > 1 ? "Send " + n + " models to Blender" : "Send to Blender";
  }

  // ------------------------------------------------------------------ choosing
  function goSlot(k) {
    if (SLOT[k].step !== S.step) $("fq").value = "";   // a new step starts with no search
    S.slot = k; S.step = SLOT[k].step; S.hover = null; renderAll();
  }
  function skippable(k) {       // nothing can go in this slot on the current model
    var sl = SLOT[k], mdl = S.models[S.cur] || {}, hk = hostKey(mdl, sl);
    if (k === "arm2" && (mdl.armR || mdl.armL)) return true;               // arms picked: no two-handed piece
    if ((k === "armR" || k === "armL") && mdl.arm2) return true;           // a two-handed piece: no single arms
    if (covered(mdl, k)) return true;
    if (hk && hk !== "torso" && hk !== "legs" && !mdl[hk]) return true;
    if (k === "wingR" || k === "wingL") {     // wings only on a back with a Wing Mount on that side
      var pk = layout(S.cur).filter(function (x) { return x.slot === "pack"; })[0];
      if (!pk || !pk.W || !socketsOf(pk)[JOINTS.Wings.adaptor[sl.sock]]) return true;
    }
    if (k === "handR" || k === "handL") {     // an arm with its weapon built in has no hand to fill
      var arm = layout(S.cur).filter(function (x) { return x.slot === hk; })[0];
      if (arm && arm.W && arm.part.anchored && !socketsOf(arm)[sl.sock]) return true;
    }
    return false;
  }
  function nextSlot() {
    // picking model by model: the same slot on the next model first
    if (!S.same && S.models.length > 1 && S.cur < S.models.length - 1) { S.cur++; S.hover = null; renderAll(); return; }
    if (!S.same && S.models.length > 1) S.cur = 0;
    var i = PICK.indexOf(S.slot);
    for (var j = i + 1; j < PICK.length; j++) {
      if (skippable(PICK[j])) continue;
      return goSlot(PICK[j]);
    }
    S.hover = null; renderAll();
    status("Squad complete: Send to Blender when you're ready.");
  }
  function setPick(k, pick) {
    var targets = S.same ? S.models.map(function (_m, i) { return i; }) : [S.cur];
    targets.forEach(function (i) {
      if (pick) S.models[i][k] = pick; else delete S.models[i][k];
      if (pick && k === "arm2") { delete S.models[i].armR; delete S.models[i].armL; }    // both arms or one piece, not both
      if (pick && (k === "armR" || k === "armL")) delete S.models[i].arm2;
    });
  }
  function choose(id) {          // a click picks; Next moves on, so you can try parts in place first
    setPick(S.slot, {id: id});
    status("");
    renderAll();
  }

  // ------------------------------------------------------------------ sending to Blender
  function requestsFor() {
    var out = [], stamp = Date.now();
    S.models.forEach(function (m, i) {
      if (!m.torso) return;
      var id = "squad-" + stamp + "-" + (i + 1);
      var placed = layout(i);
      ORDER.forEach(function (k) {
        var pk = m[k];
        if (!pk) return;
        var p = S.byId[pk.id];
        var inst = placed.filter(function (x) { return x.slot === k; })[0];
        if (!p || !inst || inst.covered) return;
        var sl = SLOT[k];
        var req = {schemaVersion: 1, path: S.libPath.replace(/[\\\/]+$/, "") + "\\" + p.path, name: p.name, title: p.name,
          category: p.type, tags: [], itemId: "", sentAt: new Date().toISOString(), model: id};
        if (k === "torso") req.at = [-i * SPACING, 0, 0];
        else if (k === "legs") { if (inst.sock) req.socket = inst.sock; }
        else req.socket = spec(p).spans ? "Shoulder R" : sl.sock;
        out.push(req);
      });
    });
    return out;
  }
  function send() {
    var reqs = requestsFor();
    if (!reqs.length) return;
    var n = 0, stamp = Date.now();
    function write(req, i) {
      var name = "sb-" + stamp + "-" + String(i).padStart(3, "0") + ".json", body = JSON.stringify(req);
      if (!S.inbHandle) { S.sentLog.push({name: name, req: req}); return Promise.resolve(); }
      return S.inbHandle.getFileHandle(name, {create: true}).then(function (fh) { return fh.createWritable(); })
        .then(function (w) { return w.write(body).then(function () { return w.close(); }); });
    }
    var chain = Promise.resolve();
    reqs.forEach(function (r, i) { chain = chain.then(function () { return write(r, i).then(function () { n++; }); }); });
    chain.then(function () {
      var models = S.models.filter(function (m) { return m.torso; }).length;
      status(window.SB_DEMO ? "Demo: " + n + " parts for " + models + " model" + (models > 1 ? "s" : "") + " would go to Blender now, each on its own model."
        : "Sent " + n + " parts for " + models + " model" + (models > 1 ? "s" : "") + (S.inbHandle ? ": Blender builds them now." : " (test mode: nothing written)."));
    }).catch(function (e) { status("Could not write to the library's _builder\\inbox: " + e.message + ". Choose the library again (Folders…)."); });
  }

  // ------------------------------------------------------------------ folders
  function setupUI(show) { $("setup").hidden = !show; $("libpath").value = S.libPath; $("adaptorn").value = S.adaptor; }
  function pickLibrary() {
    return window.showDirectoryPicker({id: "kblibrary", mode: "readwrite"}).then(function (h) {
      S.libHandle = h; idbSet("lib", h);
      return loadIndex().then(openInbox).then(function () { $("libok").innerHTML = '<span class="ok">' + S.parts.length + " parts</span>"; });
    }).catch(function (e) { $("libok").innerHTML = '<span class="err">' + esc(e.name === "NotFoundError" ? "No _builder index in that folder: run Prepare Squad Builder.bat first." : e.message) + "</span>"; });
  }
  // Parts go to Blender through the library's own _builder\inbox: browsers won't let a page
  // write into AppData, where TIOW's inbox is. TIOW Inbox 1.17.1 watches both.
  function openInbox() {
    return S.libHandle.getDirectoryHandle("_builder").then(function (b) { return b.getDirectoryHandle("inbox", {create: true}); })
      .then(function (h) { S.inbHandle = h; listening(); })
      .catch(function (e) { S.inbHandle = null; $("inbtxt").textContent = "Can't write to the library: " + e.message; });
  }
  var listenTimer = null;
  function listening() {     // TIOW Inbox touches .listening every few seconds while Blender is open
    if (listenTimer) clearTimeout(listenTimer);
    if (!S.inbHandle) return;
    S.inbHandle.getFileHandle(".listening").then(function (fh) { return fh.getFile(); })
      .then(function (f) { return Date.now() - f.lastModified < 15000; }).catch(function () { return false; })
      .then(function (on) {
        $("inbdot").classList.toggle("on", on);
        $("inbtxt").textContent = on ? "Blender listening" : "Blender not listening (open Blender with TIOW Inbox 1.17.1)";
        listenTimer = setTimeout(listening, 4000);
      });
  }
  function reconnect() {     // the browser forgets permission between visits: one click to grant it again
    return idbGet("lib").then(function (h) {
      if (!h) return false;
      return h.requestPermission({mode: "readwrite"}).then(function (p) {
        if (p !== "granted") return false;
        S.libHandle = h;
        return loadIndex().then(openInbox).then(function () { return !!S.parts.length; });
      });
    }).catch(function () { return false; });
  }

  // ------------------------------------------------------------------ events
  function bind() {
    $("steps").addEventListener("click", function (e) {
      var el = e.target.closest(".step"); if (!el) return;
      var st = STEPS[+el.getAttribute("data-i")];
      goSlot(st.key === "arms" && (S.models[S.cur] || {}).arm2 ? "arm2" : st.slots[0].k);   // a two-handed model opens on its tab
    });
    $("slotseg").addEventListener("click", function (e) { var b = e.target.closest("button"); if (b) goSlot(b.getAttribute("data-s")); });
    $("models").addEventListener("click", function (e) {
      var b = e.target.closest(".mtab"); if (b) { S.cur = +b.getAttribute("data-m"); renderAll(); }
    });
    $("models").addEventListener("change", function (e) { if (e.target.id === "samechk") { S.same = e.target.checked; } });
    $("cards").addEventListener("click", function (e) {
      var h = e.target.closest(".hide"); if (h) { e.stopPropagation(); toggleHide(S.byId[h.getAttribute("data-hide")]); return; }
      var c = e.target.closest(".card"); if (c) choose(c.getAttribute("data-id"));
    });
    $("showhid").addEventListener("change", function () {
      S.showHidden = $("showhid").checked;      // hiding mode: Hide / Unhide on the cards, hidden parts shown dimmed
      renderPicker();
    });
    $("cards").addEventListener("keydown", function (e) { if (e.key === "Enter") { var c = e.target.closest(".card"); if (c) choose(c.getAttribute("data-id")); } });
    $("cards").addEventListener("mouseover", function (e) {
      var c = e.target.closest(".card"); if (!c) return;
      var p = S.byId[c.getAttribute("data-id")];
      if (S.hover && S.hover.part === p) return;
      S.hover = {slot: S.slot, part: p};
      geometry(p.id).then(function (g) { if (g && S.hover && S.hover.part === p) redraw(); });
      redraw();
    });
    $("cards").addEventListener("mouseleave", function () { S.hover = null; redraw(); });
    ["fmaker", "fkit"].forEach(function (id) { $(id).addEventListener("change", renderPicker); });
    $("fq").addEventListener("input", renderPicker);
    $("nextbtn").addEventListener("click", nextSlot);
    $("nonebtn").addEventListener("click", function () { setPick(S.slot, null); renderAll(); });
    $("squadn").addEventListener("change", function () {
      var n = Math.max(1, Math.min(10, +$("squadn").value || 1)); $("squadn").value = n;
      if (n === S.models.length) return;      // the box fires again when it loses focus: re-drawing then would eat that click
      while (S.models.length < n) S.models.push(Object.assign({}, S.models[0]));
      S.models.length = n; if (S.cur >= n) S.cur = n - 1; framed = -1; renderAll();
    });
    $("clearbtn").addEventListener("click", function () { S.models = S.models.map(function () { return {}; }); S.cur = 0; goSlot("base"); framed = -1; status(""); });
    $("sendbtn").addEventListener("click", send);
    $("setupbtn").addEventListener("click", function () { setupUI(true); });
    $("picklib").addEventListener("click", pickLibrary);
    $("setupdone").addEventListener("click", function () {
      S.libPath = $("libpath").value.trim() || S.libPath;
      S.adaptor = Math.max(1, +$("adaptorn").value || 3);
      try { localStorage.setItem("sb.libpath", S.libPath); localStorage.setItem("sb.adaptor", String(S.adaptor)); } catch (e) { /* storage blocked: kept for this visit */ }
      renderAll();
      setupUI(false);
    });
  }

  // ------------------------------------------------------------------ start
  initView(); bind();
  window.__sb = {S: S, layout: layout, requestsFor: requestsFor, asFor: asFor, candidates: candidates, SLOT: SLOT, choose: choose, goSlot: goSlot, redraw: redraw, nextSlot: nextSlot, skippable: skippable, renderAll: renderAll, hiddenBy: hiddenBy, toggleHide: toggleHide};
  if (window.SB_DEMO) {                                       // the online demo: its own files, nothing sent
    S.source = "./";
    $("setupbtn").hidden = true;
    $("inbtxt").textContent = "Demo: Send shows what would go to Blender";
    loadIndex().catch(function (e) { status("Could not read the demo index: " + e.message); });
  } else if (params.get("lib")) {                              // served for a test: read over HTTP, nothing written
    S.source = params.get("lib").replace(/\/?$/, "/");
    loadIndex().catch(function (e) { status("Could not read the index: " + e.message); });
  } else if (!window.showDirectoryPicker) {
    setupUI(true);
    $("libok").innerHTML = '<span class="err">This browser can\'t open folders: use Chrome or Edge.</span>';
  } else {
    idbGet("lib").then(function (h) {
      if (!h) { setupUI(true); return; }
      status("Click anywhere to reconnect your library.");
      document.addEventListener("click", function once() {
        document.removeEventListener("click", once, true);
        reconnect().then(function (ok) { status(ok ? "" : "Choose your folders again (Folders…)."); if (!ok) setupUI(true); });
      }, true);
    });
  }
  renderAll();
})();
