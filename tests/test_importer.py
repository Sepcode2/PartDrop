"""Tests zonder KiCad: python tests/test_importer.py  (--net voor een echte LCSC-download)."""
import importlib.util, os, sys, zipfile, tempfile
os.environ["KICAD_CONFIG_HOME"] = tempfile.mkdtemp()
os.environ["PARTDROP_STANDALONE"] = "1"
PLUGINS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins")
spec = importlib.util.spec_from_file_location("partdrop", os.path.join(PLUGINS, "__init__.py"),
                                              submodule_search_locations=[PLUGINS])
sys.modules["partdrop"] = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sys.modules["partdrop"])
from partdrop import importer, libtable, watcher, sexpr, lcsc, i18n
i18n.set_language("en")

T = tempfile.mkdtemp()
lib = os.path.join(T, "lib")
logs = []
imp = importer.Importer(lib, "Seppe", log=logs.append, kicad_cli="")

SYM_OLD = '''(kicad_symbol_lib (version 20211014) (generator SamacSys_ECAD_Model)
  (symbol "NE555DR" (in_bom yes) (on_board yes)
    (property "Reference" "IC" (id 0) (at 0 0 0) (effects (font (size 1.27 1.27))))
    (property "Value" "NE555DR" (id 1) (at 0 0 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "SOIC127P600X175-8N" (id 2) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "https://www.ti.com/lit/ds/symlink/ne555.pdf" (id 3) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Manufacturer_Name" "Texas Instruments" (id 4) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "NE555DR_0_0" (pin passive line (at 0 0 0) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))))
  )
)'''
FP = '''(footprint "SOIC127P600X175-8N" (version 20221018) (generator pcbnew) (layer "F.Cu")
  (pad "1" smd rect (at -2.7 -1.905) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask"))
  (model "${KIPRJMOD}/NE555DR.stp" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
)'''

def mkzip(path, files):
    with zipfile.ZipFile(path, "w") as z:
        for n, c in files.items():
            z.writestr(n, c)

z1 = os.path.join(T, "LIB_NE555DR.zip")
mkzip(z1, {"NE555DR/KiCad/NE555DR.kicad_sym": SYM_OLD,
           "NE555DR/KiCad/SOIC127P600X175-8N.kicad_mod": FP,
           "NE555DR/3D/NE555DR.stp": "ISO-10303-21; dummy",
           "NE555DR/Altium/NE555DR.SchLib": "binary",
           "../../evil.txt": "zip slip"})
r = imp.import_path(z1)
print("1:", r.summary(), r.errors, r.skipped)
assert r.symbols == ["NE555DR"] and r.footprints == ["SOIC127P600X175-8N"] and not r.errors
assert not os.path.exists(os.path.join(T, "evil.txt"))

libtree = sexpr.parse(open(imp.sym_path).read())
sym = sexpr.find(libtree, "symbol")
assert str(sexpr.get_property(sym, "Footprint")[2]) == "Seppe:SOIC127P600X175-8N"
assert str(sexpr.get_property(sym, "MPN")[2]) == "NE555DR"
assert str(sexpr.get_property(sym, "Manufacturer")[2]) == "Texas Instruments"
fp = open(os.path.join(imp.pretty_dir, "SOIC127P600X175-8N.kicad_mod")).read()
assert imp.shapes_dir.replace("\\", "/") + "/NE555DR.stp" in fp, fp
print("   footprint/model/fields OK")

# 2: zelfde opnieuw → overgeslagen
r = imp.import_path(z1)
assert not r.symbols and "NE555DR" in r.skipped
print("2: skip OK", r.skipped)

# 3: SnapEDA-stijl: footprint zonder model + wrl/step, tweede symbool erbij
SYM2 = SYM_OLD.replace("NE555DR", "LM358").replace("SOIC127P600X175-8N", "SOIC-8_LM358")
FP2 = FP.replace("SOIC127P600X175-8N", "SOIC-8_LM358").split("(model")[0] + ")"
z2 = os.path.join(T, "LM358.zip")
mkzip(z2, {"LM358.kicad_sym": SYM2, "SOIC-8_LM358.kicad_mod": FP2,
           "LM358.step": "step", "LM358.wrl": "wrl"})
r = imp.import_path(z2)
print("3:", r.summary(), r.errors)
assert imp.list_symbols() == ["NE555DR", "LM358"]
fp2 = open(os.path.join(imp.pretty_dir, "SOIC-8_LM358.kicad_mod")).read()
assert "LM358.step" in fp2 and "LM358.wrl" not in fp2

# 4: legacy .lib zonder kicad-cli → nette fout, footprint wel
z3 = os.path.join(T, "old.zip")
mkzip(z3, {"KiCad/X.lib": "EESchema-LIBRARY Version 2.4\n#\n", "KiCad/X_FP.kicad_mod": FP2.replace("SOIC-8_LM358", "X_FP")})
r = imp.import_path(z3)
print("4:", r.summary(), r.errors)
assert r.footprints == ["X_FP"] and r.errors

# 5: lib-table setup
assert libtable.setup(imp, print) is True
assert libtable.setup(imp, print) is False
assert libtable.is_registered(imp)
print("5: lib-table OK:\n", open(os.path.join(os.environ["KICAD_CONFIG_HOME"], "8.0", "sym-lib-table")).read())

# 6: watcher
wd = os.path.join(T, "dl"); os.makedirs(wd)
mkzip(os.path.join(wd, "old.zip"), {"a.kicad_mod": "x"})
w = watcher.FolderWatcher(wd)
mkzip(os.path.join(wd, "new.zip"), {"a.kicad_sym": "x"})
mkzip(os.path.join(wd, "photos.zip"), {"img.jpg": "x"})
assert w.poll() == []
got = w.poll()
assert [os.path.basename(p) for p in got] == ["new.zip"], got
print("6: watcher OK")

# 7: echte LCSC download (netwerk)
if "--net" in sys.argv:
    r = lcsc.fetch("C2040", imp, log=print, python=sys.executable)
    print("7:", r.summary(), r.symbols, r.footprints, r.errors)
    libtree = sexpr.parse(open(imp.sym_path).read())
    s = [x for x in sexpr.find_all(libtree, "symbol") if str(x[1]) in r.symbols][0]
    for k in ("Footprint", "LCSC", "MPN", "Manufacturer", "Datasheet"):
        p = sexpr.get_property(s, k); print("   ", k, "=", p and str(p[2]))
    for f in r.footprints:
        txt = open(os.path.join(imp.pretty_dir, f + ".kicad_mod")).read()
        print("    model lines:", [l.strip() for l in txt.splitlines() if "(model" in l])
print("ALLES OK")
