"""Pull the add-on's numpy-only functions out of tiow_inbox.py (as fitlib does)."""
import ast, math, numpy as np
SRC = open("/home/claude/tiow_blender/tiow_inbox.py").read()
ns = {"np": np, "math": math}
for node in ast.parse(SRC).body:
    if isinstance(node, (ast.FunctionDef, ast.Assign)):
        try: exec(compile(ast.Module([node], []), "tiow_inbox", "exec"), ns)
        except Exception: pass
