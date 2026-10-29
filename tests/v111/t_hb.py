"""Helmet updates and BackPackUpdate-1 copies: every copy lands like the others, on chests from several kits."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v111/out"
AMK = "All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL"
H1 = ["All Mar All the time/HelmetsUpdate/HelmetsUpdates/HelmetsUpdates", "All Mar All the time/Outriders (1)/Outriders/Helmets-1/HelmetsUpdates/Helmets-RawSTL", "HelmetsUpdate/HelmetsUpdates/Helmets-RawSTL"]
H2 = ["All Mar All the time/HelmetsUpdate/HelmetsUpdates/HelmetsUpdates-1", "All Mar All the time/Outriders (1)/Outriders/Helmets-2/HelmetsUpdates-1/RawSTL", "HelmetsUpdates-1/HelmetsUpdates-1/RawSTL"]
BP = ["All Mar All the time/VeteranSquad/VeteranSquad/Backpacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL", "All Mar All the time/Outriders (1)/Outriders/BackPacks/BackPackUpdate-1/RawSTL", "BackPackUpdate-1/BackPackUpdate-1/RawSTL"]
CHESTS = [f"{AMK}/Chest/22-Torso-1.stl", "Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/Chest-Raw/12-Chest-1.stl", "All Mar All the time/Outriders (1)/Outriders/Torsos/RawSTL/1-Torso-A.stl",
          "All Mar All the time/Techmarine (2)/Techmarine/Chest/Chest-Raw-STL/2-Chest.stl", "All Mar All the time/ChaplainWithJumpPack (1)/ChaplainWithJumpPack/Chest/Chest-Raw-STL/2-ChestChaplain.stl"]
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def put(host, rel, cat, want, label):
    select(host); p = send(rel, cat); ck(f"{label}: {rel.split('/')[-1]} on {want}", on(p, want), T._state["last"]); return p
def rel(p, h): return A(frame(h).inverted() @ frame(p))
marines = []
# the AM helmet 1 is the same sculpt as update helmet 1: the update helmet should sit exactly where it does
select(None); t0 = send(CHESTS[0], "Bodies", (0, 0, -80)); h0 = put(t0, f"{AMK}/Helmet-Heads/1-Helmet-1.stl", "Heads", "Neck", "ref"); ref = rel(h0, t0)
b0 = put(t0, f"{BP[0]}/1.stl", "Backpacks", "Back", "ref"); refb = rel(b0, t0); tp0 = put(b0, f"{BP[0]}/7.stl", "Backpacks", "Back Top", "ref"); reft = rel(tp0, t0)
for i, chest in enumerate(CHESTS):
    for j, (hs, n, bpn, tpn) in enumerate(((H1, 1, 1, 7), (H1, 4, 2, 10), (H2, 8, 3, 12))):
        lab = f"c{i}{j}"; select(None); t = send(chest, "Bodies", (60 * i, 60 * j, 0))
        for k, d in enumerate(hs):
            h = put(t, f"{d}/{n}.stl", "Heads", "Neck", f"{lab} copy {k}")
            if h and n == 1: ck(f"{lab} copy {k}: same place as your AM helmet 1", close(rel(h, t), ref, 0.1, 0.01), f"{ang(rel(h, t), ref):.2f} deg")
        for k, d in enumerate(BP):
            b = put(t, f"{d}/{bpn}.stl", "Backpacks", "Back", f"{lab} pack copy {k}")
            if b and bpn == 1: ck(f"{lab} pack copy {k}: same as the Vet copy", close(rel(b, t), refb, 0.05, 0.01))
            if b:
                tp = put(b, f"{d}/{tpn}.stl", "Backpacks", "Back Top", f"{lab} topper copy {k}")
                if tp and tpn == 7 and bpn == 1: ck(f"{lab} topper copy {k}: same as the Vet copy", close(rel(tp, t), reft, 0.05, 0.01))
        marines.append((lab, t))
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "back": (-0.4, -1, 0.25)}
for nm, root in marines[::3]:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "hb_" + nm, obs, V, [rend.ORANGE if str(o.get("tiow_category", "")) == "Heads" else rend.BLUE if "Back" in str(o.get("tiow_category", "")) else rend.GREY for o in obs])
print("\nFAILS:", fails)
