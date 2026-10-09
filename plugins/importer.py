"""Kern van PartDrop: zet een ZIP/map/bestand om naar één eigen KiCad library.

Resultaat op schijf:
    <lib_dir>/<lib_name>.kicad_sym
    <lib_dir>/<lib_name>.pretty/
    <lib_dir>/<lib_name>.3dshapes/
"""
import os
import shutil
import tempfile
import zipfile

from . import sexpr
from .sexpr import QStr
from . import kicad_env
from .i18n import _

SYM_VERSION = "20231120"  # KiCad 8 formaat
MODEL_EXT = (".step", ".stp", ".wrl")
ALTIUM_SYM_EXT = (".schlib", ".intlib")
ALTIUM_FP_EXT = (".pcblib", ".intlib")

FIELD_ALIASES = {
    "MPN": ["MPN", "Manufacturer_Part_Number", "Mfr Part Number", "Manufacturer Part Number",
            "MP", "PartNumber", "Part Number", "Mouser Part Number"],
    "Manufacturer": ["Manufacturer", "Manufacturer_Name", "MANUFACTURER", "MF", "Mfr"],
    "LCSC": ["LCSC", "LCSC Part", "LCSC Part #", "LCSC_PN", "JLCPCB Part"],
}


class ImportResult:
    def __init__(self):
        self.symbols = []
        self.footprints = []
        self.models = []
        self.skipped = []
        self.errors = []

    @property
    def ok(self):
        return bool(self.symbols or self.footprints or self.models) and not self.errors

    def summary(self):
        parts = []
        if self.symbols:
            parts.append(_("n_symbols", len(self.symbols)))
        if self.footprints:
            parts.append(_("n_footprints", len(self.footprints)))
        if self.models:
            parts.append(_("n_models", len(self.models)))
        return ", ".join(parts) or _("nothing")


def _safe_extract(zf, dest):
    """Uitpakken met bescherming tegen zip-slip."""
    dest = os.path.realpath(dest)
    for member in zf.infolist():
        target = os.path.realpath(os.path.join(dest, member.filename))
        if not (target == dest or target.startswith(dest + os.sep)):
            continue
        if member.is_dir():
            os.makedirs(target, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with zf.open(member) as src, open(target, "wb") as out:
            shutil.copyfileobj(src, out)
        if member.filename.lower().endswith(".zip"):  # geneste ZIP (komt voor bij Mouser)
            try:
                with zipfile.ZipFile(target) as inner:
                    _safe_extract(inner, os.path.splitext(target)[0])
            except zipfile.BadZipFile:
                pass


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.write("\n")
    os.replace(tmp, path)


class Importer:
    def __init__(self, lib_dir, lib_name="MijnLib", overwrite=False, prefer_step=True,
                 log=print, kicad_cli=None):
        self.lib_dir = os.path.abspath(lib_dir)
        self.lib_name = lib_name
        self.overwrite = overwrite
        self.prefer_step = prefer_step
        self.log = log
        self.kicad_cli = kicad_cli if kicad_cli is not None else kicad_env.find_kicad_cli()

    # --- paden -------------------------------------------------------------
    @property
    def sym_path(self):
        return os.path.join(self.lib_dir, self.lib_name + ".kicad_sym")

    @property
    def pretty_dir(self):
        return os.path.join(self.lib_dir, self.lib_name + ".pretty")

    @property
    def shapes_dir(self):
        return os.path.join(self.lib_dir, self.lib_name + ".3dshapes")

    def ensure_library(self):
        os.makedirs(self.pretty_dir, exist_ok=True)
        os.makedirs(self.shapes_dir, exist_ok=True)
        if not os.path.exists(self.sym_path):
            lib = ["kicad_symbol_lib", ["version", SYM_VERSION],
                   ["generator", QStr("partdrop")], ["generator_version", QStr("8.0")]]
            _write_atomic(self.sym_path, sexpr.dumps(lib))

    # --- publieke ingang ---------------------------------------------------
    def import_path(self, path, fields=None):
        """Importeer een ZIP, map of los bestand. fields: extra symboolvelden."""
        res = ImportResult()
        self.ensure_library()
        work = tempfile.mkdtemp(prefix="partdrop_")
        try:
            src = os.path.join(work, "src")
            os.makedirs(src)
            if os.path.isdir(path):
                shutil.copytree(path, src, dirs_exist_ok=True)
            elif zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as zf:
                    _safe_extract(zf, src)
            elif os.path.isfile(path):
                shutil.copy2(path, src)
            else:
                res.errors.append(_("file_missing", path))
                return res
            self._import_dir(src, work, res, fields or {})
        except Exception as e:  # nooit KiCad laten crashen
            res.errors.append("%s: %s" % (type(e).__name__, e))
        finally:
            shutil.rmtree(work, ignore_errors=True)
        return res

    # --- scannen -----------------------------------------------------------
    def _scan(self, root):
        found = {"sym": [], "legacy": [], "fp": [], "model": [], "alt_sym": [], "alt_fp": []}
        for dp, _dn, fns in os.walk(root):
            for fn in fns:
                p = os.path.join(dp, fn)
                low = fn.lower()
                if low.endswith(".kicad_sym"):
                    found["sym"].append(p)
                elif low.endswith(".lib"):
                    with open(p, "rb") as f:
                        if f.read(64).startswith(b"EESchema-LIBRARY"):
                            found["legacy"].append(p)
                elif low.endswith(".kicad_mod"):
                    found["fp"].append(p)
                elif low.endswith(MODEL_EXT):
                    found["model"].append(p)
                if low.endswith(ALTIUM_SYM_EXT):
                    found["alt_sym"].append(p)
                if low.endswith(ALTIUM_FP_EXT):
                    found["alt_fp"].append(p)
        return found

    def _import_dir(self, src, work, res, fields):
        f = self._scan(src)
        conv = os.path.join(work, "conv")
        os.makedirs(conv)

        # Symbolen: KiCad > legacy > Altium
        if f["sym"]:
            # naar KiCad 8 formaat brengen (indien kicad-cli beschikbaar), anders origineel
            sym_files = [self._cli_sym(p, conv) or p for p in f["sym"]]
        elif f["legacy"]:
            sym_files = [x for x in (self._cli_sym(p, conv) for p in f["legacy"]) if x]
        elif f["alt_sym"]:
            self.log(_("altium_sym"))
            sym_files = [x for x in (self._cli_sym(p, conv) for p in f["alt_sym"]) if x]
        else:
            sym_files = []
        if (f["legacy"] or f["alt_sym"]) and not sym_files and not self.kicad_cli:
            res.errors.append(_("needs_cli"))

        # Footprints: KiCad > Altium
        fp_files = list(f["fp"])
        if not fp_files and f["alt_fp"]:
            self.log(_("altium_fp"))
            for p in f["alt_fp"]:
                fp_files += self._convert_altium_fp(p, conv)

        if not (sym_files or fp_files or f["model"]):
            res.errors.append(_("nothing_usable"))
            return

        models = self._copy_models(f["model"], res)
        fp_names = self._copy_footprints(fp_files, models, res)
        for p in sym_files:
            self._merge_symbols(p, fp_names, fields, res)

    # --- conversie ---------------------------------------------------------
    def _cli_sym(self, path, outdir):
        if not self.kicad_cli:
            if not path.lower().endswith(".kicad_sym"):
                self.log(_("cli_cant_convert", os.path.basename(path)))
            return None
        out = os.path.join(outdir, "%d_%s.kicad_sym" % (len(os.listdir(outdir)),
                                                      os.path.splitext(os.path.basename(path))[0]))
        code, msg = kicad_env.run([self.kicad_cli, "sym", "upgrade", "--force", path, "-o", out])
        if code != 0 or not os.path.exists(out):
            self.log(_("sym_upgrade_failed", os.path.basename(path), msg.strip()))
            return None
        return out

    def _convert_altium_fp(self, path, outdir):
        pretty = os.path.join(outdir, os.path.splitext(os.path.basename(path))[0] + ".pretty")
        if self.kicad_cli:
            code, msg = kicad_env.run([self.kicad_cli, "fp", "upgrade", "--force", path, "-o", pretty])
            if code == 0 and os.path.isdir(pretty):
                return [os.path.join(pretty, x) for x in os.listdir(pretty) if x.endswith(".kicad_mod")]
            self.log(_("fp_upgrade_failed", msg.strip()))
        # fallback via de pcbnew python API (alleen binnen KiCad)
        try:
            import pcbnew
            io = pcbnew.PCB_IO_MGR.PluginFind(pcbnew.PCB_IO_MGR.ALTIUM_DESIGNER)
            os.makedirs(pretty, exist_ok=True)
            for name in io.FootprintEnumerate(path):
                fp = io.FootprintLoad(path, name)
                pcbnew.FootprintSave(pretty, fp)
            return [os.path.join(pretty, x) for x in os.listdir(pretty) if x.endswith(".kicad_mod")]
        except Exception as e:
            self.log(_("altium_fp_failed", e))
            return []

    # --- 3D ----------------------------------------------------------------
    def _copy_models(self, paths, res):
        """Kopieer modellen, geeft dict stem(lower) -> doelpad (beste extensie)."""
        rank = {".step": 0, ".stp": 0, ".wrl": 1} if self.prefer_step else {".wrl": 0, ".step": 1, ".stp": 1}
        best = {}
        for p in paths:
            stem, ext = os.path.splitext(os.path.basename(p))
            dest = os.path.join(self.shapes_dir, os.path.basename(p))
            if os.path.exists(dest) and not self.overwrite:
                res.skipped.append(os.path.basename(p))
            else:
                shutil.copy2(p, dest)
                res.models.append(os.path.basename(p))
            key = stem.lower()
            if key not in best or rank[ext.lower()] < rank[os.path.splitext(best[key])[1].lower()]:
                best[key] = dest
        return best

    def _model_path(self, dest):
        return dest.replace("\\", "/")

    # --- footprints --------------------------------------------------------
    def _copy_footprints(self, paths, models, res):
        names = []
        seen = set()
        for p in paths:
            name = os.path.splitext(os.path.basename(p))[0]
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            dest = os.path.join(self.pretty_dir, name + ".kicad_mod")
            names.append(name)
            if os.path.exists(dest) and not self.overwrite:
                res.skipped.append(name + ".kicad_mod")
                continue
            try:
                tree = sexpr.parse(_read(p))
            except ValueError as e:
                res.errors.append(_("fp_unreadable", name, e))
                continue
            self._fix_models(tree, name, models, single=len(paths) == 1)
            _write_atomic(dest, sexpr.dumps(tree))
            res.footprints.append(name)
        return names

    def _fix_models(self, fp, fp_name, models, single):
        if not models:
            return
        existing = sexpr.find_all(fp, "model")
        for m in existing:
            stem = os.path.splitext(os.path.basename(str(m[1]).replace("\\", "/")))[0].lower()
            target = models.get(stem)
            if target is None and len(models) == 1:
                target = next(iter(models.values()))
            if target:
                m[1] = QStr(self._model_path(target))
        if not existing:
            target = models.get(fp_name.lower())
            if target is None and single and len(models) == 1:
                target = next(iter(models.values()))
            if target:
                fp.append(["model", QStr(self._model_path(target)),
                           ["offset", ["xyz", "0", "0", "0"]],
                           ["scale", ["xyz", "1", "1", "1"]],
                           ["rotate", ["xyz", "0", "0", "0"]]])

    # --- symbolen ----------------------------------------------------------
    def _merge_symbols(self, path, fp_names, fields, res):
        try:
            src = sexpr.parse(_read(path))
        except ValueError as e:
            res.errors.append(_("sym_unreadable", e))
            return
        lib = sexpr.parse(_read(self.sym_path))
        index = {str(s[1]): i for i, s in enumerate(lib) if sexpr.tag(s) == "symbol"}
        changed = False
        for sym in sexpr.find_all(src, "symbol"):
            name = str(sym[1])
            if name in res.symbols:  # zelfde symbool in meerdere formaten in de ZIP
                continue
            if name in index and not self.overwrite:
                res.skipped.append(name)
                continue
            if sexpr.find(sym, "extends") is None:
                self._fix_symbol(sym, fp_names, fields)
            if name in index:
                lib[index[name]] = sym
            else:
                lib.append(sym)
                index[name] = len(lib) - 1
            res.symbols.append(name)
            changed = True
        if changed:
            _write_atomic(self.sym_path, sexpr.dumps(lib))

    def _fix_symbol(self, sym, fp_names, fields):
        name = str(sym[1])
        # Footprint koppelen aan de eigen library
        fpp = sexpr.get_property(sym, "Footprint")
        current = str(fpp[2]).split(":")[-1] if fpp is not None else ""
        lookup = {n.lower(): n for n in fp_names}
        target = lookup.get(current.lower())
        if target is None and len(fp_names) == 1:
            target = fp_names[0]
        if target:
            sexpr.set_property(sym, "Footprint", "%s:%s" % (self.lib_name, target))

        # Velden normaliseren: MPN, Manufacturer, LCSC
        for key, aliases in FIELD_ALIASES.items():
            if fields.get(key):
                sexpr.set_property(sym, key, fields[key])
                continue
            if sexpr.get_property(sym, key) is not None and str(sexpr.get_property(sym, key)[2]):
                continue
            for a in aliases:
                p = sexpr.get_property(sym, a)
                if p is not None and str(p[2]).strip():
                    sexpr.set_property(sym, key, str(p[2]))
                    break
            else:
                if key == "MPN":
                    sexpr.set_property(sym, "MPN", name)
        if fields.get("Datasheet"):
            sexpr.set_property(sym, "Datasheet", fields["Datasheet"])
        for k, v in fields.items():
            if k not in FIELD_ALIASES and k != "Datasheet" and v:
                sexpr.set_property(sym, k, v)

    # --- library info ------------------------------------------------------
    def list_symbols(self):
        if not os.path.exists(self.sym_path):
            return []
        lib = sexpr.parse(_read(self.sym_path))
        return [str(s[1]) for s in sexpr.find_all(lib, "symbol")]
