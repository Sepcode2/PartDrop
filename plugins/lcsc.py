"""LCSC/EasyEDA import via easyeda2kicad (als apart proces, dus geen licentie-vermenging
en geen risico dat een fout in die library KiCad laat crashen)."""
import os
import re
import shutil
import tempfile

from . import kicad_env
from .i18n import _

LCSC_RE = re.compile(r"^C\d{3,}$", re.IGNORECASE)


def normalize_id(text):
    t = text.strip().upper()
    if t.isdigit():
        t = "C" + t
    return t if LCSC_RE.match(t) else None


def is_installed(python):
    code, _out = kicad_env.run([python, "-c", "import easyeda2kicad"], timeout=60)
    return code == 0


def install(python, log=print):
    log(_("installing"))
    code, out = kicad_env.run([python, "-m", "pip", "install", "--user", "--upgrade", "easyeda2kicad"],
                              timeout=600)
    log(out.strip().splitlines()[-1] if out.strip() else "")
    return code == 0


def fetch(lcsc_id, importer, log=print, python=None):
    """Download een component en importeer het in de eigen library."""
    from .importer import ImportResult
    res = ImportResult()
    pid = normalize_id(lcsc_id)
    if not pid:
        res.errors.append(_("invalid_lcsc", lcsc_id))
        return res
    python = python or kicad_env.find_python()
    if not python:
        res.errors.append(_("no_python"))
        return res
    if not is_installed(python) and not install(python, log):
        res.errors.append(_("install_failed"))
        return res

    work = tempfile.mkdtemp(prefix="partdrop_lcsc_")
    try:
        out = os.path.join(work, "lcsc")
        log(_("fetching", pid))
        code, msg = kicad_env.run([python, "-m", "easyeda2kicad", "--full",
                                   "--lcsc_id=%s" % pid, "--output", out, "--overwrite"], timeout=300)
        produced = [p for p in os.listdir(work)]
        if not produced:
            res.errors.append(_("e2k_empty", msg.strip()[-800:]))
            return res
        if code != 0:
            log(_("e2k_error", msg.strip()[-400:]))
        return importer.import_path(work, fields={"LCSC": pid})
    finally:
        shutil.rmtree(work, ignore_errors=True)
