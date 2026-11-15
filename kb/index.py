"""The Squad Builder's _builder/index.json, changed in place so Josh needn't run Prepare.

Prepare writes it compact; since Nov 6 ASCII-escaped, before that UTF-8. load() works out which and dump() writes the
same, so an index that wasn't changed comes back byte-identical (load() refuses a file it can't reproduce).
Standard library only; build_index (squad-builder/) is imported only when a part's entry is rebuilt."""
import json, os, sys
from . import REPO


class Index:
    def __init__(self, raw):
        self.d = json.loads(raw)
        for a in (True, False):
            if json.dumps(self.d, separators=(",", ":"), ensure_ascii=a).encode("utf-8") == raw: self.ascii = a; break
        else: raise ValueError("index.json isn't in a form this can write back identically; run Prepare instead")
        self.by_path = {e["path"]: e for e in self.d["parts"]}

    @classmethod
    def load(cls, path): return cls(open(path, "rb").read())

    def dumps(self): return json.dumps(self.d, separators=(",", ":"), ensure_ascii=self.ascii).encode("utf-8")

    def update_part(self, path, sidecar_data):
        """Refresh one part's fits / sockets / exact / adaptor from its (new) sidecar. path as in the index."""
        sys.path.insert(0, os.path.join(REPO, "squad-builder")); import build_index
        e = self.by_path[path]; e.update(build_index.part_data(sidecar_data))
        if e.get("variants") and sidecar_data.get("variants"):      # the maker's copies too, as build() lists them
            for ve in e["variants"]:
                v = sidecar_data["variants"][ve["i"]] if isinstance(ve.get("i"), int) and ve["i"] < len(sidecar_data["variants"]) else None
                if not isinstance(v, dict) or not isinstance(v.get("sidecar"), dict): continue
                ve["align"] = build_index.flat16(v.get("align")) or ve["align"]
                d = build_index.part_data(v["sidecar"]); d.pop("category", None)
                for k in ("fits", "sockets", "noPad", "noHand", "adaptor", "exact", "upright", "offHand", "scale"): ve.pop(k, None)
                ve.update(d)
        return e

    def add_parts(self, entries, joints=None):
        """Entries from build_index.build() on a small folder of new parts. Refuses paths already there."""
        dup = [e["path"] for e in entries if e["path"] in self.by_path]
        if dup: raise ValueError("already in the index: %s" % dup[:5])
        self.d["parts"].extend(entries); self.by_path.update({e["path"]: e for e in entries})
        if joints and isinstance(self.d.get("joints"), dict): self.d["joints"].update(joints)
        return len(entries)
