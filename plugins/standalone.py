"""PartDrop los starten (zonder PCB editor), bv. naast de schema editor.

Starten met de Python van KiCad, zodat wxPython beschikbaar is:
    Windows:  "C:\\Program Files\\KiCad\\8.0\\bin\\pythonw.exe" standalone.py
    macOS:    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 standalone.py
    Linux:    python3 standalone.py   (met python3-wxgtk4.0 geïnstalleerd)
De knop 'Snelkoppeling maken' in PartDrop doet dit allemaal voor je.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_package():
    """De pluginmap heet na PCM-installatie bv. 'be_fme-projects_partdrop' en is dus
    geen geldige modulenaam; daarom laden we hem expliciet als 'partdrop'."""
    os.environ["PARTDROP_STANDALONE"] = "1"  # __init__ registreert dan geen ActionPlugin
    spec = importlib.util.spec_from_file_location(
        "partdrop", os.path.join(HERE, "__init__.py"), submodule_search_locations=[HERE])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["partdrop"] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    load_package()
    import wx
    app = wx.App(False)
    app.SetAppName("PartDrop")
    from partdrop import gui
    gui.show(None)
    app.MainLoop()


if __name__ == "__main__":
    main()
