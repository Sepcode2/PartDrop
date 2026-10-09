"""Alles wat met de KiCad-installatie te maken heeft: paden, kicad-cli, python."""
import os
import shutil
import subprocess
import sys

KICAD_VERSION_DIR = "8.0"


def config_dir():
    """Map met sym-lib-table, fp-lib-table en kicad_common.json."""
    try:
        import pcbnew  # noqa
        p = pcbnew.SETTINGS_MANAGER.GetUserSettingsPath()
        if p and os.path.isdir(p):
            return p
    except Exception:
        pass
    env = os.environ.get("KICAD_CONFIG_HOME")
    if env:
        return os.path.join(env, KICAD_VERSION_DIR)
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "kicad", KICAD_VERSION_DIR)
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Preferences/kicad/" + KICAD_VERSION_DIR)
    base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(base, "kicad", KICAD_VERSION_DIR)


def _exe_dir():
    return os.path.dirname(os.path.abspath(sys.executable))


def _no_window():
    if sys.platform.startswith("win"):
        return {"creationflags": 0x08000000}  # CREATE_NO_WINDOW
    return {}


def find_kicad_cli():
    names = ["kicad-cli.exe", "kicad-cli"]
    candidates = [os.path.join(_exe_dir(), n) for n in names]
    if sys.platform == "darwin":
        candidates.append("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
    if sys.platform.startswith("win"):
        for pf in (os.environ.get("ProgramFiles", r"C:\Program Files"),):
            candidates.append(os.path.join(pf, "KiCad", KICAD_VERSION_DIR, "bin", "kicad-cli.exe"))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return shutil.which("kicad-cli")


def find_python():
    """De python van KiCad (binnen pcbnew is sys.executable vaak kicad.exe)."""
    exe = os.path.basename(sys.executable).lower()
    if exe.startswith("python"):
        return sys.executable
    for n in ("python.exe", "python3", "python"):
        c = os.path.join(_exe_dir(), n)
        if os.path.isfile(c):
            return c
    if sys.platform == "darwin":
        c = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
        if os.path.isfile(c):
            return c
    return shutil.which("python3") or shutil.which("python")


def run(cmd, timeout=180):
    """Voert een commando uit, geeft (returncode, output) terug."""
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout, **_no_window())
        return p.returncode, p.stdout.decode("utf-8", "replace")
    except FileNotFoundError:
        return 127, "Niet gevonden: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return 124, "Timeout: %s" % " ".join(cmd)
