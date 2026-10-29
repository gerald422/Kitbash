// Adds "Send to Blender" and library part types to TIOW-FTRP.
//
//   node apply-blender-bridge.mjs                    patch %LOCALAPPDATA%\TIOW-FTRP
//   node apply-blender-bridge.mjs --library "E:\Library\_library.json"
//                                                    take part types from your library file
//   node apply-blender-bridge.mjs --check            report only, change nothing
//   node apply-blender-bridge.mjs --undo             put the original files back
//   (pass a folder path to target a different TIOW-FTRP install)
//
// Close TIOW-FTRP first and start it again afterwards: the server file is only
// read at start-up. Re-run after updating TIOW-FTRP, because an update
// replaces the patched files, and re-run after changing part types in
// _library.json. Every anchor must appear exactly once, or nothing is written.
// An install patched by an older version of this script is upgraded from its
// saved originals.
//
// What it adds:
//   * "Send to Blender" in the right-click menu and in the item details panel,
//     and double-click a card to send it straight away.
//   * POST /api/local/blender on the local server. It resolves the item through
//     the server's existing safe() check, so a request can only name files
//     inside a connected folder, and writes one small JSON request file to
//     local-data\blender-inbox. The TIOW Inbox add-on in Blender picks it up.
//   * Library part types: a file's category comes from the nearest folder whose
//     name is a known part type (Pistols, Two-Handed Guns, Arms-RawStl, ...)
//     before TIOW's own filename rules. Blender files each import into a
//     collection with that name. Applies to files TIOW adds to a catalogue
//     after patching, so patch before connecting the library.

import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const undo = args.includes('--undo'), check = args.includes('--check');
let libraryFile = null;
const positional = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--library') { libraryFile = args[++i]; continue; }
  if (!args[i].startsWith('--')) positional.push(args[i]);
}
const dir = positional[0] || path.join(process.env.LOCALAPPDATA || '', 'TIOW-FTRP');
const MARK = 'tiow-blender-bridge';          // any version
const VERSION = 'tiow-blender-bridge:v4';    // this version (v4: library part types Hands, Two-Handed Held, ...)
const BACKUP = '.pre-blender-bridge';
const END = Symbol('append');

// Part types and the folder names that mean them. Must match _library.json.
const DEFAULT_TYPES = {
  "Arms": ["arms", "arm"],
  "Heads": ["heads", "head", "helmets", "helmet"],
  "Chests": ["chests", "chest", "torsos", "torso", "bodies", "body"],
  "Legs": ["legs", "leg", "predesigned legs"],
  "Backpacks": ["backpacks", "backpack"],
  "Jump Packs": ["jump packs", "jump pack", "jumppacks", "jumppack"],
  "Shoulder Pads": ["shoulder pads", "shoulder pad", "shoulderpads", "shoulderpad", "pauldrons", "pauldron"],
  "Knee Pads": ["knee pads", "knee pad", "kneepads", "kneepad", "shin pads", "shin pad", "shinpads", "shinpad", "greaves", "greave"],
  "Melee": ["melee", "one handed melee"],
  "Pistols": ["pistols", "pistol"],
  "Heavy Weapons": ["heavy weapons", "heavy weapon"],
  "Two-Handed Guns": ["two handed guns", "two armed guns"],
  "Two-Handed Melee": ["two handed melee", "two armed melee"],
  "Shields": ["shields", "shield"],
  "Accessories": ["accessories", "accesories"],
  "Bases": ["bases", "base", "roundbase", "roundbase32mm"],
  "Mechadendrites": ["mechadendrites", "mechadendrite"],
  "Servo Skulls": ["servo skulls", "servo skull"],
  "Trophies": ["trophies", "trophy"],
  "Seals": ["seals", "seal", "purity seals", "purityseals"],
  "Grenades": ["grenades", "grenade"],
  "Hands": ["hands", "hand"],
  "Hand-less Weapons": ["hand-less weapons", "handless weapons"],
  "Two-Handed Held": ["two handed held"],
  "Backpack Toppers": ["backpack toppers", "backpack topper"],
  "Heavy Weapon Cables": ["heavy weapon cables"],
  "Cables": ["cables", "cable"],
  "Pack Fins": ["pack fins", "pack fin"],
  "Bikes": ["bikes", "bike"],
  "Bike Parts": ["bike parts"],
  "Servo Arms": ["servo arms", "servo arm"],
  "Adapters": ["adapters", "adapter", "adaptors", "adaptor"],
  "Forearm Armour": ["forearm armour", "forearm armor", "forearms", "forearm", "vambraces", "vambrace"],
  "Cloaks": ["cloaks", "cloak", "capes", "cape"]
};

// Trailing words creators add to slot folders: Arms-RawStl-Mirrored -> arms.
const STRIP = ['raw', 'rawstl', 'stl', 'mirrored', 'mirror', 'sergeant', 'support', 'supported', 'presupported'];
const norm = s => {
  const w = String(s).toLowerCase().replace(/[_\-\s]+/g, ' ').trim().split(' ');
  while (w.length > 1 && STRIP.includes(w[w.length - 1])) w.pop();
  return w.join(' ');
};

function typeMap() {
  let types = DEFAULT_TYPES;
  if (libraryFile) {
    const lib = JSON.parse(fs.readFileSync(libraryFile, 'utf8'));
    types = {};
    for (const [type, spec] of Object.entries(lib.partTypes || {}))
      types[type] = Array.isArray(spec) ? spec : (spec.aliases || []);
    if (!Object.keys(types).length) throw Error(`No partTypes in ${libraryFile}`);
  }
  const map = {};
  for (const [type, aliases] of Object.entries(types))
    for (const a of [type, ...aliases]) map[norm(a)] = type;
  return map;
}

const SERVER_ROUTE = `/*${VERSION}*/if(route==='/api/local/blender'&&req.method==='POST'){if(!(await fs.stat(target)).isFile())throw Error('Select an existing file');const meta=await body(req),inbox=path.join(path.dirname(configFile),'blender-inbox'),text=v=>String(v??'').slice(0,500);await fs.mkdir(inbox,{recursive:true});const job={schemaVersion:1,path:target,name:path.basename(target),title:text(meta.title),category:text(meta.category),tags:Array.isArray(meta.tags)?meta.tags.slice(0,50).map(text):[],itemId:text(meta.itemId),sentAt:new Date().toISOString()};const file=path.join(inbox,Date.now()+'-'+crypto.randomUUID()+'.json');await fs.writeFile(file+'.tmp',JSON.stringify(job));await fs.rename(file+'.tmp',file);let listening=false;try{listening=Date.now()-(await fs.stat(path.join(inbox,'.listening'))).mtimeMs<10000;}catch{}json(res,{ok:true,listening});return;}`;

const appTail = map => `
/*${VERSION}*/
async function sendToBlender(item){const entry=item&&findEntry(item);if(typeof entry?.handle?.sendToBlender!=='function'){toast('Connect this item’s folder through the local viewer first.');return;}try{const r=await entry.handle.sendToBlender({title:item.title,category:item.category,tags:item.tags,itemId:item.id});toast(r.listening?'Sent to Blender: '+item.name:'Queued for Blender: '+item.name+'. Blender isn’t listening: open it with the TIOW Inbox add-on enabled.');}catch(e){toast('Could not send to Blender: '+e.message);}}
$('send-item').onclick=()=>{const item=contextItem;closeItemMenu();sendToBlender(item);};
let blenderLastClick={id:null,t:0};
$('results').addEventListener('click',e=>{const card=e.target.closest('[data-id]');if(!card)return;const now=performance.now();if(blenderLastClick.id===card.dataset.id&&now-blenderLastClick.t<450){blenderLastClick={id:null,t:0};sendToBlender(state.items.find(i=>i.id===card.dataset.id));}else blenderLastClick={id:card.dataset.id,t:now};});
function libraryPartType(path){const types=${JSON.stringify(map)},strip=${JSON.stringify(STRIP)};for(const f of String(path).split('/').slice(0,-1).reverse()){const w=f.toLowerCase().replace(/[_\\-\\s]+/g,' ').trim().split(' ');while(w.length>1&&strip.includes(w[w.length-1]))w.pop();const t=types[w.join(' ')];if(t)return t;}return null;}
`;
// Double-click is detected by hand: selecting a card re-renders the grid, so
// the second click lands on a new element and the browser never fires dblclick.

const ACTIONS = `\${entry?'<button id="download-model">Save local file</button>':'<button id="connect-selected" class="primary">Connect folder</button>'}`;

const edits = map => ({
  'local-folder-server.mjs': [
    ["const target=await safe(id,relative);", SERVER_ROUTE],
  ],
  'dist/local-folder-bridge.js': [
    ["async reveal(){await call('reveal',{id:this.id,path:this.path,method:'POST'});}",
     `/*${VERSION}*/async sendToBlender(meta){return(await(await call('blender',{id:this.id,path:this.path,method:'POST',data:meta})).json());}`],
  ],
  'dist/index.html': [
    ['<button id="reveal-item" role="menuitem">Open in Explorer</button>',
     `<!--${VERSION}--><button id="send-item" role="menuitem">Send to Blender</button>`],
  ],
  'dist/app.js': [
    ["$('reveal-item').disabled=!canReveal;", "$('send-item').disabled=!canReveal;"],
    [ACTIONS, `\${typeof entry?.handle?.sendToBlender==='function'?'<button id="send-to-blender">Send to Blender</button>':''}`],
    ["$('edit-item-tags').onclick=()=>openTagEditor(item);",
     "if($('send-to-blender'))$('send-to-blender').onclick=()=>sendToBlender(item);"],
    ["function guessCategory(path){", "{const t=libraryPartType(path);if(t)return t;}"],
    [END, appTail(map)],
  ],
});

const count = (s, sub) => s.split(sub).length - 1;
function writeAtomic(file, text) {
  fs.writeFileSync(file + '.tmp', text);
  fs.renameSync(file + '.tmp', file);
}

if (!fs.existsSync(path.join(dir, 'local-folder-server.mjs'))) {
  console.error(`TIOW-FTRP not found in ${dir} - pass its folder as an argument.`);
  process.exit(1);
}

const EDITS = edits(undo ? {} : typeMap());

if (undo) {
  let restored = 0;
  for (const rel of Object.keys(EDITS)) {
    const file = path.join(dir, rel), backup = file + BACKUP;
    if (!fs.existsSync(backup)) continue;
    if (!check) { fs.copyFileSync(backup, file); fs.unlinkSync(backup); }
    restored++;
    console.log(`${check ? 'would restore' : 'restored'}  ${rel}`);
  }
  console.log(restored ? 'Done. Restart TIOW-FTRP.' : 'Nothing to undo.');
  process.exit(0);
}

// Plan everything first; write only if every file is safe to patch.
const plan = [];
for (const [rel, list] of Object.entries(EDITS)) {
  const file = path.join(dir, rel), backup = file + BACKUP;
  const current = fs.readFileSync(file, 'utf8');
  if (current.includes(VERSION) && !libraryFile) { console.log(`already patched  ${rel}`); continue; }
  let src = current, upgrade = false;
  if (current.includes(MARK)) {
    // patched before (older version, or new part types): start again from the original
    if (!fs.existsSync(backup)) {
      console.error(`ABORT: ${rel} is patched but its original (${path.basename(backup)}) is missing.`);
      process.exit(1);
    }
    src = fs.readFileSync(backup, 'utf8');
    upgrade = true;
  }
  let out = src;
  for (const [anchor, insert] of list) {
    if (anchor === END) { out += insert; continue; }
    const n = count(out, anchor);
    if (n !== 1) {
      console.error(`ABORT: anchor found ${n}x in ${rel} (expected once) - this TIOW-FTRP build `
        + `differs from the one the patch was written for. Nothing was changed.\n  ${anchor}`);
      process.exit(1);
    }
    out = out.replace(anchor, () => anchor + insert);   // function form: no $-pattern expansion
  }
  if (out === current) { console.log(`already patched  ${rel}`); continue; }
  plan.push([rel, file, backup, src, out, upgrade]);
}

for (const [rel, file, backup, src, out, upgrade] of plan) {
  if (check) { console.log(`would ${upgrade ? 're-patch' : 'patch'}  ${rel}`); continue; }
  if (!upgrade) fs.writeFileSync(backup, src);           // keep the true original
  writeAtomic(file, out);
  console.log(`${upgrade ? 're-patched' : 'patched'}  ${rel}  (original kept as ${path.basename(backup)})`);
}
if (!check && plan.length) console.log('Done. Restart TIOW-FTRP to load the new server route.');
