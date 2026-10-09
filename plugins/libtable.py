"""Voegt de eigen library automatisch toe aan de globale sym-lib-table en fp-lib-table."""
import os
import shutil
import time

from . import sexpr
from .sexpr import QStr
from . import kicad_env
from .i18n import _


def _ensure_entry(table_path, root_tag, name, uri, descr):
    """Geeft 'added', 'updated' of 'present' terug."""
    if os.path.exists(table_path):
        with open(table_path, encoding="utf-8") as f:
            tree = sexpr.parse(f.read())
    else:
        tree = [root_tag, ["version", "7"]]
    for lib in sexpr.find_all(tree, "lib"):
        n = sexpr.find(lib, "name")
        if n and str(n[1]) == name:
            u = sexpr.find(lib, "uri")
            if u and str(u[1]) == uri:
                return "present"
            u[1] = QStr(uri)
            status = "updated"
            break
    else:
        tree.append(["lib", ["name", QStr(name)], ["type", QStr("KiCad")], ["uri", QStr(uri)],
                     ["options", QStr("")], ["descr", QStr(descr)]])
        status = "added"
    if os.path.exists(table_path):
        shutil.copy2(table_path, table_path + ".partdrop-backup")
    else:
        os.makedirs(os.path.dirname(table_path), exist_ok=True)
    tmp = table_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(sexpr.dumps(tree) + "\n")
    os.replace(tmp, table_path)
    return status


def setup(importer, log=print):
    """Registreer symbool- en footprintlibrary. True als KiCad herstart moet worden."""
    importer.ensure_library()
    cfg = kicad_env.config_dir()
    name = importer.lib_name
    descr = _("lib_descr")
    s1 = _ensure_entry(os.path.join(cfg, "sym-lib-table"), "sym_lib_table", name,
                       importer.sym_path.replace("\\", "/"), descr)
    s2 = _ensure_entry(os.path.join(cfg, "fp-lib-table"), "fp_lib_table", name,
                       importer.pretty_dir.replace("\\", "/"), descr)
    for table, s in (("sym-lib-table", s1), ("fp-lib-table", s2)):
        if s == "present":
            log(_("table_present", table, name))
        else:
            log(_("table_added" if s == "added" else "table_updated", table, name, cfg))
    return s1 != "present" or s2 != "present"


def is_registered(importer):
    cfg = kicad_env.config_dir()
    for fn in ("sym-lib-table", "fp-lib-table"):
        p = os.path.join(cfg, fn)
        if not os.path.exists(p):
            return False
        with open(p, encoding="utf-8") as f:
            tree = sexpr.parse(f.read())
        want = (importer.sym_path if fn == "sym-lib-table" else importer.pretty_dir).replace("\\", "/")
        if not any(sexpr.find(l, "name") and sexpr.find(l, "uri")
                   and str(sexpr.find(l, "name")[1]) == importer.lib_name
                   and str(sexpr.find(l, "uri")[1]).replace("\\", "/") == want
                   for l in sexpr.find_all(tree, "lib")):
            return False
    return True


def registered_dir(name):
    """Map waar de symboollibrary 'name' volgens KiCad staat, of None."""
    p = os.path.join(kicad_env.config_dir(), "sym-lib-table")
    try:
        with open(p, encoding="utf-8") as f:
            tree = sexpr.parse(f.read())
    except (OSError, ValueError):
        return None
    for lib in sexpr.find_all(tree, "lib"):
        n, u = sexpr.find(lib, "name"), sexpr.find(lib, "uri")
        if n and u and str(n[1]) == name and "${" not in str(u[1]):
            return os.path.dirname(str(u[1])) or None
    return None
