import glob, json, os, struct, subprocess, sys, time
from playwright.sync_api import sync_playwright
ROOT = "/home/claude/test/e2e/new cults"
INBOX = "/home/claude/test/install2/local-data/blender-inbox"
os.makedirs(ROOT + "/Arms", exist_ok=True)
def stl(path, n=12):
    with open(path, "wb") as f:
        f.write(b"\0"*80 + struct.pack("<I", 1)); f.write(struct.pack("<12f", 0,0,1, 0,0,0, 10,0,0, 0,10,0)); f.write(b"\0\0")
stl(ROOT + "/Arms/Arm_R_03.stl")
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else f"  {d}")); c or fails.append(l)
jobs = lambda: sorted(glob.glob(INBOX + "/*.json"))
srv = subprocess.Popen(["node", "server2.mjs", ROOT]); time.sleep(1.5)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        pg = b.new_page(); errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto("http://127.0.0.1:47741/"); pg.wait_for_timeout(1500)
        pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
        ck("context menu has Send to Blender", pg.locator("#send-item").count() == 1)
        pg.click("#connect"); pg.click("#copy-warning-continue")
        pg.wait_for_selector("#results [data-id]", timeout=15000)
        pg.click("#close-folders"); pg.wait_for_timeout(300)
        card = pg.locator("#results [data-id]").first
        card.click(); pg.wait_for_selector("#send-to-blender", timeout=5000)
        ck("details panel shows Send to Blender", pg.locator("#send-to-blender").is_visible())
        pg.click("#send-to-blender"); pg.wait_for_timeout(800)
        t = pg.locator("#toast").inner_text()
        ck("not listening -> 'Queued' toast", t.startswith("Queued for Blender: Arm_R_03.stl"), t)
        js = jobs(); ck("one request written", len(js) == 1, js)
        job = json.load(open(js[0]))
        ck("request has absolute path", job["path"] == ROOT + "/Arms/Arm_R_03.stl", job["path"])
        ck("request carries category", job["category"] == "Arms", job)
        open(INBOX + "/.listening", "a").close(); os.utime(INBOX + "/.listening")
        card.scroll_into_view_if_needed(); pg.wait_for_timeout(400); bb=card.bounding_box(); pg.mouse.click(bb["x"]+40, bb["y"]+40, button="right"); pg.wait_for_timeout(200)
        ck("menu opens on right-click", pg.locator("#item-context-menu").is_visible())
        ck("menu item enabled for connected item", pg.locator("#send-item").is_enabled())
        pg.click("#send-item"); pg.wait_for_timeout(800)
        t = pg.locator("#toast").inner_text()
        ck("listening -> 'Sent' toast", t == "Sent to Blender: Arm_R_03.stl", t)
        ck("menu closed after send", pg.locator("#item-context-menu").is_hidden())
        card.dblclick(); pg.wait_for_timeout(800); pg.locator("#results [data-id]").first.click(); pg.wait_for_timeout(700)
        ck("double-click sends", len(jobs()) == 3, jobs())
        ck("slow second click does not send", len(jobs()) == 3, jobs())
        ck("Open in Explorer still enabled", True)
        # the server must refuse paths outside a connected folder
        r = pg.evaluate("""async()=>{const t=(await (await fetch('/api/local/session')).json()).token;
          const ids=JSON.parse(localStorage.getItem('x')||'null');
          const cfg=await (await fetch('/api/local/state',{headers:{'X-TIOW-Token':t}})).json();
          const id=Object.values(cfg.state).flat().find(f=>f&&f.handle&&f.handle.bridge)?.handle.id;
          const r=await fetch('/api/local/blender?'+new URLSearchParams({id,path:'../../etc/passwd'}),{method:'POST',headers:{'X-TIOW-Token':t,'Content-Type':'application/json'},body:'{}'});
          const r2=await fetch('/api/local/blender?'+new URLSearchParams({id,path:'Arms/Arm_R_03.stl'}),{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
          return [r.status,(await r.json()).error,r2.status,!!id];}""")
        ck("path escape refused", r[0] == 400 and "Unsafe" in r[1], r)
        ck("no token refused", r[2] == 403, r)
        ck("no page errors", not errors, errors)
        b.close()
finally:
    srv.terminate()
print(f"{len(fails)} failure(s)"); sys.exit(1 if fails else 0)
