#!/usr/bin/env python3
"""joints.json is the one table of part types: the joint each type lands on, the folder words that mean the type,
and old socket names. Edit joints.json, then run this.

  python3 tools/gen_joints.py            rewrite what is generated from it:
                                           addons/tiow_inbox.py   DEFAULT_JOINTS / DEFAULT_ALIASES (only if they differ)
                                           bridge/_library.json   "joints", "jointAliases" (its own "partTypes" are
                                                                  TIOW's folder words, wider on purpose: only checked
                                                                  to list every type)
                                           library-tools/partTypes.json
  python3 tools/gen_joints.py --check    change nothing; exit 1 if any of those, or the page's JOINTS table
                                         (squad-builder/src/app.js) or plan_names.py's short names, disagree.
The page's table is checked, not written: a new type on the page needs a step designed for it anyway, and the check
makes sure the line you add there says the same as joints.json. Standard library only."""
import ast, json, os, re, sys
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = lambda *a: os.path.join(R, *a)
ADDON, PAGE, LIBJ, PT, NAMES = (P("addons", "tiow_inbox.py"), P("squad-builder", "src", "app.js"),
                                P("bridge", "_library.json"), P("library-tools", "partTypes.json"),
                                P("library-tools", "plan_names.py"))
PAGE_KEYS = ("socket", "sided", "mirrorLeft", "spans", "adaptor")     # what the page's table carries


def addon_tables(src):
    """DEFAULT_JOINTS and DEFAULT_ALIASES as the add-on has them, with the source span of each."""
    env, out = {}, {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("BELT", "BIKE", "DEFAULT_JOINTS", "DEFAULT_ALIASES"):
                env[name] = eval(compile(ast.Expression(node.value), "addon", "eval"), {}, dict(env))
                out[name] = (env[name], node.lineno, node.end_lineno)
    return out


def py_literal(name, d):
    lines = ["%s = {" % name]
    for k, v in d.items():
        lines.append("    %s: %s," % (json.dumps(k), json.dumps(v).replace("true", "True").replace("false", "False")))
    return lines + ["}"]


def page_table(src):
    m = re.search(r"var JOINTS = (\{.*?\n  \});", src, re.S)
    t = re.sub(r"//[^\n]*", "", m.group(1))
    t = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', t)
    return json.loads(t)


def main():
    check = "--check" in sys.argv
    J = json.load(open(P("joints.json"), encoding="utf-8"))
    joints, aliases, types = J["joints"], J["aliases"], J["partTypes"]
    bad, wrote = [], []
    src = open(ADDON, encoding="utf-8").read()
    T = addon_tables(src)
    if T["DEFAULT_JOINTS"][0] != joints or T["DEFAULT_ALIASES"][0] != aliases:
        if check: bad.append("addons/tiow_inbox.py DEFAULT_JOINTS / DEFAULT_ALIASES differ from joints.json")
        else:
            L = src.split("\n")
            for name, d in sorted((("DEFAULT_JOINTS", joints), ("DEFAULT_ALIASES", aliases)),
                                  key=lambda x: -T[x[0]][1]):          # lower block first, so line numbers hold
                if T[name][0] != d: L[T[name][1] - 1:T[name][2]] = py_literal(name, d)
            open(ADDON, "w", encoding="utf-8", newline="\n").write("\n".join(L))
            import subprocess
            subprocess.check_call([sys.executable, P("tools", "build_addon.py"), "--split"])
            wrote.append("addons/tiow_inbox.py and its sections (bump its version and deliver it)")
    lib = json.load(open(LIBJ, encoding="utf-8"))
    want = dict(lib, joints=joints, jointAliases=aliases)
    if want != lib:
        if check: bad.append("bridge/_library.json joints / jointAliases differ from joints.json")
        else:
            open(LIBJ, "w", encoding="utf-8", newline="\n").write(json.dumps(want, indent=2, ensure_ascii=False) + "\n")
            wrote.append("bridge/_library.json (deliver it to the bridge folder)")
    if json.load(open(PT, encoding="utf-8")) != types:
        if check: bad.append("library-tools/partTypes.json differs from joints.json")
        else:
            open(PT, "w", encoding="utf-8", newline="\n").write(json.dumps(types, indent=1, ensure_ascii=False) + "\n")
            wrote.append("library-tools/partTypes.json")
    for t, e in page_table(open(PAGE, encoding="utf-8").read()).items():
        if t not in joints: bad.append("page JOINTS has %r, joints.json hasn't" % t); continue
        for k in PAGE_KEYS:
            if k in e and e[k] != joints[t].get(k):
                bad.append("page JOINTS %r %s = %r, joints.json %r" % (t, k, e[k], joints[t].get(k)))
    known = set(joints) | set(J.get("noJoint", []))
    for t in types:
        if t not in known: bad.append("partTypes has %r, which is neither a joint nor in noJoint" % t)
    for t in types:
        if t not in lib.get("partTypes", {}) and t != "Unsorted": bad.append("bridge/_library.json partTypes lacks %r" % t)
    names = open(NAMES, encoding="utf-8").read()
    short = [t for t in sorted(known) if '"%s"' % t not in names and "'%s'" % t not in names]
    for w in wrote: print("wrote", w)
    if short: print("note: no short name in plan_names.py for: " + ", ".join(short))
    if bad: print("\n".join(bad)); sys.exit(1)
    print("joints.json: %d joints, %d part types, all in step" % (len(joints), len(types)))


if __name__ == "__main__":
    main()
