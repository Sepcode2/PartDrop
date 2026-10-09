"""PartDrop – componenten importeren in één eigen KiCad library (KiCad 8)."""
import os

try:
    if os.environ.get("PARTDROP_STANDALONE"):
        raise ImportError("los gestart, geen ActionPlugin nodig")
    import pcbnew
    import wx

    class PartDropAction(pcbnew.ActionPlugin):
        def defaults(self):
            self.name = "PartDrop"
            self.category = "Libraries"
            self.description = "Importeer componenten (LCSC, SnapEDA, Ultra Librarian, Samacsys, Altium…) in je eigen library"
            self.show_toolbar_button = True
            self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.png")

        def Run(self):
            from . import gui
            parent = next((w for w in wx.GetTopLevelWindows() if w.GetName() == "PcbFrame"), None)
            gui.show(parent)

    PartDropAction().register()
except Exception as e:  # buiten KiCad (tests) of bij een fout: niet crashen
    import logging
    logging.getLogger(__name__).debug("PartDrop niet geregistreerd: %s", e)
