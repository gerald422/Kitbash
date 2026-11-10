"""Build a delivery for tools/kb.py apply. One way to put files on the PC, whatever the task.

    from kb import deliver
    d = deliver.Delivery("pads-2026-11-10", out_dir)
    d.new("lib", "Bits/X/Part.sockets.json", data)                 # must not exist yet
    d.replace("lib", "_builder/index.json", data, base_md5)        # base_md5: the file the work started from
    d.append("lib", "_sources.csv", rows_bytes, base_md5, base_bytes=...)   # add to the end of a file
    d.copy("nc", "Maker/a.stl", "lib", "Maker - Mark/Kit/Heads/Maker Kit - Helmet 1.stl", md5)   # stays on the PC
    files = d.build()       # writes manifest.json + payload-NN.tgz (<= 12 MB each); returns the files to commit

Then: device_commit_files those into  <library>\\_backups\\<task>\\deliver\\  and on the PC
    python3 kb.py apply ".../_backups/<task>/deliver" --check     and again without --check.
apply checks, backs up, writes and md5-verifies; see tools/kb.py. Standard library only."""
import hashlib, io, json, os, tarfile

CHUNK = 12 * 10 ** 6           # device_commit_files takes files up to ~14 MB reliably


def md5b(b): return hashlib.md5(b).hexdigest()


class Delivery:
    def __init__(self, task, out_dir):
        self.task, self.out, self.files, self.blobs = task, out_dir, [], {}

    def _add(self, mode, root, path, data, **kw):
        member = "f/%05d" % len(self.blobs)
        self.blobs[member] = data
        self.files.append(dict(mode=mode, root=root, path=path.replace("\\", "/"), md5=md5b(data), member=member, **kw))

    def new(self, root, path, data): self._add("new", root, path, data)

    def replace(self, root, path, data, base_md5): self._add("replace", root, path, data, base=base_md5)

    def append(self, root, path, data, base_md5, base_bytes):
        if md5b(base_bytes) != base_md5: raise ValueError("base_bytes isn't the base file: " + path)
        self._add("append", root, path, data, base=base_md5, after=md5b(base_bytes + data))

    def copy(self, from_root, from_path, root, path, md5):
        self.files.append(dict(mode="copy", from_root=from_root, **{"from": from_path.replace("\\", "/")},
                               root=root, path=path.replace("\\", "/"), md5=md5))

    def build(self):
        os.makedirs(self.out, exist_ok=True)
        names, cur, size = [], [], 0
        groups = []
        for m, b in self.blobs.items():
            if cur and size + len(b) > CHUNK: groups.append(cur); cur, size = [], 0
            cur.append((m, b)); size += len(b)
        if cur: groups.append(cur)
        for i, g in enumerate(groups):
            n = "payload-%02d.tgz" % i; names.append(n)
            with tarfile.open(os.path.join(self.out, n), "w:gz") as t:
                for m, b in g:
                    ti = tarfile.TarInfo(m); ti.size = len(b); t.addfile(ti, io.BytesIO(b))
        man = {"task": self.task, "payload": names, "files": self.files,
               "payload_md5": {n: md5b(open(os.path.join(self.out, n), "rb").read()) for n in names}}
        open(os.path.join(self.out, "manifest.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(man, indent=1))
        return [os.path.join(self.out, n) for n in ["manifest.json"] + names]
