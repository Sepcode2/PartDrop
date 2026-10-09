"""Maakt dist/PartDrop-<versie>.zip voor KiCad PCM 'Install from File'."""
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))

meta = json.load(open(os.path.join(ROOT, "metadata.json"), encoding="utf-8"))
version = meta["versions"][0]["version"]
os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
out = os.path.join(ROOT, "dist", "PartDrop-%s.zip" % version)

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(ROOT, "metadata.json"), "metadata.json")
    z.write(os.path.join(ROOT, "resources", "icon.png"), "resources/icon.png")
    for fn in sorted(os.listdir(os.path.join(ROOT, "plugins"))):
        if fn.endswith((".py", ".png", ".ico")):
            z.write(os.path.join(ROOT, "plugins", fn), "plugins/" + fn)
print(out)
