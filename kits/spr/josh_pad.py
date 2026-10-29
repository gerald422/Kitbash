"""Josh's hand-placed 62 on 'patternC heavy Rarm 4' (actual.blend, Oct 20) -> reference Pad R anchor."""
import json, numpy as np, sys
sys.path.insert(0, '/home/claude/real'); import fitlib as F
from spr_arms import S_R
import spr_pads as SP
new = {r["name"]: r for r in json.load(open("/home/claude/blend/objects_oct20.json"))}
G = json.load(open("G.json"))
REL = "patternC arms/heavy weapons/patternC heavy Rarm 4.stl"
mw_pad = np.array(new["62-ShoulderPad-1"]["mw"]); mw_arm = np.array(new["patternC heavy Rarm 4"]["mw"])
Gm = np.array(G["patternC heavy Rarm 4"]["G"])
X = np.linalg.inv(mw_arm @ Gm) @ mw_pad                     # pad in the arm's scaled file coordinates
s = json.load(open(SP.ST + REL[:-4] + ".sockets.json"))
W = S_R @ np.array(s["fits"]["Shoulder R"]).reshape(4, 4)
A_josh = W @ X @ np.linalg.inv(SP.F62)                      # Pad R anchor implied by Josh's pad (torso coords, our arm placement)
A_mine = W @ np.array(next(x["matrix"] for x in s["sockets"] if x["type"] == "Pad R")).reshape(4, 4)
if __name__ == "__main__":
    print("arm: Josh's placement vs ours: %.3f mm" % np.linalg.norm((mw_arm @ Gm)[:3, 3] - W[:3, 3]))
    d = np.linalg.inv(A_mine) @ A_josh
    print("Josh vs first try (in the anchor frame): move %s mm (|%.2f|), turn %.1f deg" % (d[:3, 3].round(2), np.linalg.norm(d[:3, 3]), F.ang(d[:3, :3])))
    print("Josh pad centre (torso):", (W @ X @ np.r_[SP._pad_center(), 1])[:3].round(2), " first try:", (A_mine @ SP.F62 @ np.r_[SP._pad_center(), 1])[:3].round(2))
    json.dump({"A_josh_torso": A_josh.tolist(), "X_arm": X.tolist()}, open("w/josh_pad_h4.json", "w"))
