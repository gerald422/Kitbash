"""Put the Squad Builder page together: one HTML file with three.js inside, so it opens offline."""
import os
H = os.path.dirname(os.path.abspath(__file__))
src = lambda p: open(os.path.join(H, p), encoding="utf-8").read()
page = src("src/shell.html")
for mark, body in (("/*CSS*/", src("src/app.css")), ("/*THREE*/", src("vendor/three/build/three.min.js")),
                   ("/*ORBIT*/", src("vendor/three/examples/js/controls/OrbitControls.js")), ("/*APP*/", src("src/app.js"))):
    page = page.replace(mark, body.replace("</script", "<\\/script"), 1)
out = os.path.join(H, "Squad Builder.html")
open(out, "w", encoding="utf-8").write(page)
print(out, len(page))
