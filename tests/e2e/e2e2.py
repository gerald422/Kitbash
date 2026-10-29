import glob, json, os, struct, subprocess, sys, time, shutil
from playwright.sync_api import sync_playwright
ROOT = "/home/claude/test/e2e/Mar Fil - Weapons"
INBOX = "/home/claude/test/install2/local-data/blender-inbox"
shutil.rmtree(ROOT, ignore_errors=True); shutil.rmtree("/home/claude/test/install2/local-data", ignore_errors=True)
files = {"Two-Handed Guns/70-Gun-1-A.stl": "Two-Handed Guns", "Pistols/211-BoltPistol-R.stl": "Pistols",
         "Melee/175-ChainSword-1-R.stl": "Melee", "Two-Handed Melee/145-PowerAxe-1-1-B.stl": "Two-Handed Melee",
         "Heavy Weapons/121-HeavyGun-A.stl": "Heavy Weapons", "Shields/211-Shield-R.stl": "Shields",
         "Unsorted guns/plasma_gun.stl": "Weapons", "Arms/Arms-RawStl/73-Arm-1.stl": "Arms"}
for rel in files:
    p = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(b"\0"*80 + struct.pack("<I", 1) + struct.pack("<12f", 0,0,1, 0,0,0, 10,0,0, 0,10,0) + b"\0\0")
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else f"  {d}")); c or fails.append(l)
srv = subprocess.Popen(["node", "server2.mjs", ROOT]); time.sleep(1.5)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        pg = b.new_page(); errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto("http://127.0.0.1:47741/"); pg.wait_for_timeout(1500); pg.keyboard.press("Escape")
        pg.click("#connect"); pg.click("#copy-warning-continue")
        pg.wait_for_selector("#results [data-id]", timeout=15000); pg.click("#close-folders"); pg.wait_for_timeout(300)
        got = pg.evaluate("""()=>[...document.querySelectorAll('#results [data-id]')].map(c=>[c.querySelector('h3').textContent,c.querySelector('.category').textContent.split(' · ')[0]])""")
        cats = {t.replace(' ', '_') if False else t: c for t, c in got}
        for rel, want in files.items():
            title = os.path.basename(rel)[:-4].replace('_', ' ').replace('-', ' ')
            ck(f"{rel} -> {want}", cats.get(title) == want, cats.get(title))
        opts = pg.evaluate("()=>[...document.querySelectorAll('#category option')].map(o=>o.value).filter(Boolean)")
        ck("Item type filter lists the weapon types", all(t in opts for t in ["Melee","Pistols","Heavy Weapons","Two-Handed Guns","Two-Handed Melee"]), opts)
        pg.select_option("#category", "Two-Handed Guns"); pg.wait_for_timeout(300)
        card = pg.locator("#results [data-id]").first
        ck("filter shows just the two-handed gun", pg.locator("#results [data-id]").count() == 1)
        card.dblclick(); pg.wait_for_timeout(800)
        js = sorted(glob.glob(INBOX + "/*.json"))
        job = json.load(open(js[-1])) if js else {}
        ck("request carries category Two-Handed Guns", job.get("category") == "Two-Handed Guns", job.get("category"))
        ck("no page errors", not errors, errors)
        b.close()
finally:
    srv.terminate()
print(f"{len(fails)} failure(s)"); sys.exit(1 if fails else 0)
