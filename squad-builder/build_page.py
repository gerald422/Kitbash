"""Put the Squad Builder page together: one HTML file with three.js inside, so it opens offline.

  python build_page.py            write Squad Builder.html
  python build_page.py --check    change nothing; exit 1 if Squad Builder.html isn't what src/ builds"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
src = lambda p: open(os.path.join(H, p), encoding="utf-8").read()
page = src("src/shell.html")
for mark, body in (("/*CSS*/", src("src/app.css")), ("/*THREE*/", src("vendor/three/build/three.min.js")),
                   ("/*ORBIT*/", src("vendor/three/examples/js/controls/OrbitControls.js")), 
                   ("/*XFORM*/", src("vendor/three/examples/js/controls/TransformControls.js")), ("/*APP*/", src("src/app.js"))):
    page = page.replace(mark, body.replace("</script", "<\\/script"), 1)
out = os.path.join(H, "Squad Builder.html")
if "--check" in sys.argv:
    if not os.path.exists(out) or open(out, encoding="utf-8", newline="").read() != page:
        print("squad-builder/Squad Builder.html isn't what src/ builds: run squad-builder/build_page.py"); sys.exit(1)
    print("the page matches its sources"); sys.exit(0)
open(out, "w", encoding="utf-8", newline="").write(page)
print(out, len(page))
