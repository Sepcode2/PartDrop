"""Houdt een map (bv. Downloads) in het oog en meldt nieuwe component-ZIP's."""
import os
import zipfile

INTERESTING = (".kicad_sym", ".kicad_mod", ".lib", ".step", ".stp", ".wrl",
               ".schlib", ".pcblib", ".intlib")


def looks_like_component(path):
    try:
        with zipfile.ZipFile(path) as zf:
            names = [n.lower() for n in zf.namelist()]
    except (zipfile.BadZipFile, OSError):
        return False
    has_eda = any(n.endswith(INTERESTING[:2]) or n.endswith(INTERESTING[6:]) for n in names)
    has_lib = any(n.endswith(".lib") for n in names)
    has_model = any(n.endswith((".step", ".stp", ".wrl")) for n in names)
    nested = any(n.endswith(".zip") for n in names)
    return has_eda or (has_lib and has_model) or nested


class FolderWatcher:
    """Pollen i.p.v. OS-events: werkt overal en heeft geen extra dependencies nodig."""

    def __init__(self, folder):
        self.folder = folder
        self._sizes = {}
        self._known = set(self._zips())  # wat er al stond, negeren we

    def _zips(self):
        try:
            return [os.path.join(self.folder, f) for f in os.listdir(self.folder)
                    if f.lower().endswith(".zip")]
        except OSError:
            return []

    def poll(self):
        """Geeft nieuwe, volledig gedownloade component-ZIP's terug."""
        ready = []
        for p in self._zips():
            if p in self._known:
                continue
            try:
                size = os.path.getsize(p)
            except OSError:
                continue
            if self._sizes.get(p) == size and size > 0:  # grootte stabiel = download klaar
                self._known.add(p)
                self._sizes.pop(p, None)
                if looks_like_component(p):
                    ready.append(p)
            else:
                self._sizes[p] = size
        return ready
