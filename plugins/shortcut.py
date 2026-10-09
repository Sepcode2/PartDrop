"""Maakt een snelkoppeling om PartDrop los te starten (bureaublad + Startmenu)."""
import os
import stat
import sys

from . import kicad_env
from .i18n import _

HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCHER = os.path.join(HERE, "standalone.py")


def _gui_python():
    py = kicad_env.find_python()
    if py and sys.platform.startswith("win"):
        w = os.path.join(os.path.dirname(py), "pythonw.exe")  # geen zwart consolevenster
        if os.path.isfile(w):
            return w
    return py


def _ps_quote(s):
    return "'" + s.replace("'", "''") + "'"


def create(log=print):
    """Geeft een lijst met aangemaakte paden terug."""
    py = _gui_python()
    if not py:
        raise RuntimeError(_("no_python"))
    made = []

    if sys.platform.startswith("win"):
        icon = os.path.join(HERE, "icon.ico")
        lines = ["$sh = New-Object -ComObject WScript.Shell"]
        targets = ["[Environment]::GetFolderPath('Desktop')",
                   "[Environment]::GetFolderPath('Programs')"]
        for folder in targets:
            lines += [
                "$p = Join-Path (%s) 'PartDrop.lnk'" % folder,
                "$s = $sh.CreateShortcut($p)",
                "$s.TargetPath = %s" % _ps_quote(py),
                "$s.Arguments = %s" % _ps_quote('"%s"' % LAUNCHER),
                "$s.WorkingDirectory = %s" % _ps_quote(HERE),
                "$s.IconLocation = %s" % _ps_quote(icon),
                "$s.Description = %s" % _ps_quote(_("title")),
                "$s.Save()",
                "Write-Output $p",
            ]
        code, out = kicad_env.run(["powershell", "-NoProfile", "-NonInteractive",
                                   "-ExecutionPolicy", "Bypass", "-Command", "; ".join(lines)], timeout=60)
        if code != 0:
            raise RuntimeError(_("shortcut_failed", out.strip()))
        made = [l.strip() for l in out.splitlines() if l.strip().lower().endswith(".lnk")]

    elif sys.platform == "darwin":
        p = os.path.expanduser("~/Desktop/PartDrop.command")
        with open(p, "w") as f:
            f.write('#!/bin/sh\nexec "%s" "%s"\n' % (py, LAUNCHER))
        os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        made.append(p)

    else:
        entry = ("[Desktop Entry]\nType=Application\nName=PartDrop\n"
                 "Comment=%s\n" % _("title") +
                 'Exec="%s" "%s"\nIcon=%s\nTerminal=false\nCategories=Development;Electronics;\n'
                 % (py, LAUNCHER, os.path.join(HERE, "icon.png")))
        apps = os.path.expanduser("~/.local/share/applications")
        os.makedirs(apps, exist_ok=True)
        for d in (apps, os.path.expanduser("~/Desktop")):
            if os.path.isdir(d):
                p = os.path.join(d, "partdrop.desktop")
                with open(p, "w") as f:
                    f.write(entry)
                os.chmod(p, 0o755)
                made.append(p)

    for p in made:
        log(_("shortcut_log", p))
    return made
