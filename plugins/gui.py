"""wxPython venster van PartDrop."""
import os
import queue
import subprocess
import sys
import threading

import wx

from . import config, libtable, lcsc, kicad_env, shortcut, i18n
from .i18n import _
from .importer import Importer
from .watcher import FolderWatcher

_instance = None


class _DropTarget(wx.FileDropTarget):
    def __init__(self, on_files):
        super().__init__()
        self.on_files = on_files

    def OnDropFiles(self, x, y, filenames):
        self.on_files(list(filenames))
        return True


class PartDropDialog(wx.Frame):
    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT if parent else wx.DEFAULT_FRAME_STYLE
        self.cfg = config.load()
        i18n.set_language(i18n.detect(self.cfg.get("language", "auto")))  # vóór het bouwen van het venster
        super().__init__(parent, title=_("title"), size=(640, 700), style=style)
        self.jobs = queue.Queue()
        self.watcher = None
        self._build()
        self._apply_cfg()
        self._apply_on_top()
        icon = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon):
            self.SetIcon(wx.Icon(icon, wx.BITMAP_TYPE_PNG))
        threading.Thread(target=self._worker, daemon=True).start()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self.timer)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self._update_watch()
        self._update_reg_status()
        self.log(_("log_library", self._importer(self.log).sym_path))
        cli = kicad_env.find_kicad_cli()
        self.log("kicad-cli: %s" % (cli or _("cli_missing")))

    # --- opbouw ------------------------------------------------------------
    def _build(self):
        p = wx.Panel(self)
        root = wx.BoxSizer(wx.VERTICAL)

        # Library
        box = wx.StaticBoxSizer(wx.VERTICAL, p, _("box_lib"))
        g = wx.FlexGridSizer(2, 2, 6, 8)
        g.AddGrowableCol(1)
        g.Add(wx.StaticText(p, label=_("name")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.lib_name = wx.TextCtrl(p)
        g.Add(self.lib_name, 1, wx.EXPAND)
        g.Add(wx.StaticText(p, label=_("folder")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.lib_dir = wx.DirPickerCtrl(p, style=wx.DIRP_USE_TEXTCTRL)
        g.Add(self.lib_dir, 1, wx.EXPAND)
        box.Add(g, 0, wx.EXPAND | wx.ALL, 4)
        row = wx.BoxSizer(wx.HORIZONTAL)
        self.reg_btn = wx.Button(p, label=_("register"))
        self.reg_status = wx.StaticText(p, label="")
        open_btn = wx.Button(p, label=_("open_folder"))
        sc_btn = wx.Button(p, label=_("shortcut_btn"))
        sc_btn.SetToolTip(_("shortcut_tip"))
        row.Add(self.reg_btn, 0, wx.RIGHT, 8)
        row.Add(self.reg_status, 1, wx.ALIGN_CENTER_VERTICAL)
        row.Add(sc_btn, 0, wx.RIGHT, 6)
        row.Add(open_btn, 0)
        box.Add(row, 0, wx.EXPAND | wx.ALL, 4)
        root.Add(box, 0, wx.EXPAND | wx.ALL, 8)

        # LCSC
        box = wx.StaticBoxSizer(wx.HORIZONTAL, p, _("box_lcsc"))
        self.lcsc_id = wx.TextCtrl(p, style=wx.TE_PROCESS_ENTER)
        self.lcsc_id.SetHint(_("lcsc_hint"))
        lcsc_btn = wx.Button(p, label=_("import_btn"))
        box.Add(self.lcsc_id, 1, wx.EXPAND | wx.ALL, 4)
        box.Add(lcsc_btn, 0, wx.ALL, 4)
        root.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        # Drop zone
        self.drop = wx.Panel(p, size=(-1, 110), style=wx.BORDER_THEME)
        self.drop.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))
        ds = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(self.drop, label=_("drop_text"),
                            style=wx.ALIGN_CENTER_HORIZONTAL)
        pick = wx.Button(self.drop, label=_("pick_btn"))
        ds.AddStretchSpacer()
        ds.Add(lbl, 0, wx.ALIGN_CENTER | wx.ALL, 4)
        ds.Add(pick, 0, wx.ALIGN_CENTER | wx.ALL, 4)
        ds.AddStretchSpacer()
        self.drop.SetSizer(ds)
        for w in (self.drop, lbl):
            w.SetDropTarget(_DropTarget(self._queue_files))
        root.Add(self.drop, 0, wx.EXPAND | wx.ALL, 8)

        # Watcher + opties
        box = wx.StaticBoxSizer(wx.VERTICAL, p, _("box_auto"))
        row = wx.BoxSizer(wx.HORIZONTAL)
        self.watch = wx.CheckBox(p, label=_("watch"))
        self.watch_dir = wx.DirPickerCtrl(p, style=wx.DIRP_USE_TEXTCTRL)
        row.Add(self.watch, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row.Add(self.watch_dir, 1, wx.EXPAND)
        box.Add(row, 0, wx.EXPAND | wx.ALL, 4)
        self.delete_after = wx.CheckBox(p, label=_("delete_after"))
        self.overwrite = wx.CheckBox(p, label=_("overwrite"))
        self.prefer_step = wx.CheckBox(p, label=_("prefer_step"))
        self.on_top = wx.CheckBox(p, label=_("on_top"))
        opts = wx.GridSizer(2, 2, 4, 12)  # 2x2 zodat niets afgesneden wordt
        for c in (self.delete_after, self.overwrite, self.prefer_step, self.on_top):
            opts.Add(c, 0)
        box.Add(opts, 0, wx.ALL, 4)
        row = wx.BoxSizer(wx.HORIZONTAL)
        self._lang_codes = ["auto"] + list(i18n.LANGS)
        self.lang = wx.Choice(p, choices=[_("lang_auto")] + [i18n.NAMES[c] for c in i18n.LANGS])
        row.Add(wx.StaticText(p, label=_("language")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row.Add(self.lang, 0)
        box.Add(row, 0, wx.ALL, 4)
        root.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        # Log
        self.log_ctrl = wx.TextCtrl(p, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        root.Add(self.log_ctrl, 1, wx.EXPAND | wx.ALL, 8)
        p.SetSizer(root)

        self.reg_btn.Bind(wx.EVT_BUTTON, self._on_register)
        open_btn.Bind(wx.EVT_BUTTON, self._on_open_dir)
        sc_btn.Bind(wx.EVT_BUTTON, self._on_shortcut)
        self.on_top.Bind(wx.EVT_CHECKBOX, lambda e: self._apply_on_top())
        self.lang.Bind(wx.EVT_CHOICE, self._on_language)
        lcsc_btn.Bind(wx.EVT_BUTTON, self._on_lcsc)
        self.lcsc_id.Bind(wx.EVT_TEXT_ENTER, self._on_lcsc)
        pick.Bind(wx.EVT_BUTTON, self._on_pick)
        self.watch.Bind(wx.EVT_CHECKBOX, lambda e: self._update_watch())
        self.watch_dir.Bind(wx.EVT_DIRPICKER_CHANGED, lambda e: self._update_watch())
        self.lib_name.Bind(wx.EVT_TEXT, lambda e: self._update_reg_status())
        self.lib_dir.Bind(wx.EVT_DIRPICKER_CHANGED, lambda e: self._update_reg_status())

    def _apply_cfg(self):
        c = self.cfg
        self.lib_name.SetValue(c["lib_name"])
        # Lege map (bug in 0.1/0.2): neem de map over die al in KiCad geregistreerd staat
        lib_dir = c["lib_dir"] or libtable.registered_dir(c["lib_name"]) or config.DEFAULTS["lib_dir"]
        c["lib_dir"] = lib_dir
        try:
            os.makedirs(lib_dir, exist_ok=True)  # DirPicker toont een niet-bestaande map als leeg
        except OSError:
            pass
        self.lib_dir.SetPath(lib_dir)
        self.watch_dir.SetPath(c["watch_dir"])
        self.watch.SetValue(c["watch"])
        self.delete_after.SetValue(c["delete_after_import"])
        self.overwrite.SetValue(c["overwrite"])
        self.prefer_step.SetValue(c["prefer_step"])
        self.on_top.SetValue(c.get("stay_on_top", False))
        lang = c.get("language", "auto")
        self.lang.SetSelection(self._lang_codes.index(lang) if lang in self._lang_codes else 0)

    def _read_cfg(self):
        name = "".join(ch for ch in self.lib_name.GetValue().strip() if ch.isalnum() or ch in "_-") or "MijnLib"
        lib_dir = self.lib_dir.GetPath().strip() or self.cfg.get("lib_dir") or config.DEFAULTS["lib_dir"]
        self.cfg.update(lib_name=name, lib_dir=lib_dir,
                        watch_dir=self.watch_dir.GetPath().strip() or self.cfg.get("watch_dir", ""),
                        watch=self.watch.GetValue(), delete_after_import=self.delete_after.GetValue(),
                        overwrite=self.overwrite.GetValue(), prefer_step=self.prefer_step.GetValue(),
                        stay_on_top=self.on_top.GetValue(),
                        language=self._lang_codes[max(self.lang.GetSelection(), 0)])
        return self.cfg

    def _importer(self, log, c=None):
        c = c or self._read_cfg()
        return Importer(c["lib_dir"], c["lib_name"], overwrite=c["overwrite"],
                        prefer_step=c["prefer_step"], log=log)

    # --- log (thread-safe) -------------------------------------------------
    def log(self, msg):
        if wx.IsMainThread():
            self._append(msg)
        else:
            wx.CallAfter(self._append, msg)

    def _append(self, msg):
        try:
            if self and self.log_ctrl:  # venster kan al gesloten zijn
                self.log_ctrl.AppendText(msg + "\n")
        except RuntimeError:
            pass

    # --- acties ------------------------------------------------------------
    def _update_reg_status(self):
        try:
            ok = libtable.is_registered(self._importer(self.log))
        except Exception:
            ok = False
        self.reg_status.SetLabel(_("registered") if ok else _("not_registered"))

    def _on_register(self, evt):
        try:
            if libtable.setup(self._importer(self.log), self.log):
                wx.MessageBox(_("reg_done"), "PartDrop", wx.ICON_INFORMATION, self)
        except Exception as e:
            self.log(_("reg_failed", e))
        self._update_reg_status()

    def _apply_on_top(self):
        style = self.GetWindowStyle()
        if self.on_top.GetValue():
            style |= wx.STAY_ON_TOP
        else:
            style &= ~wx.STAY_ON_TOP
        self.SetWindowStyle(style)

    def _on_shortcut(self, evt):
        try:
            made = shortcut.create(self.log)
            wx.MessageBox(_("shortcut_done", "\n".join(made)), "PartDrop", wx.ICON_INFORMATION, self)
        except Exception as e:
            self.log("  ✖ %s" % e)

    def _on_language(self, evt):
        config.save(self._read_cfg())
        self.log(_("lang_restart"))

    def _on_open_dir(self, evt):
        d = self._importer(self.log).lib_dir
        os.makedirs(d, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(d)
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", d])

    def _on_lcsc(self, evt):
        ids = self.lcsc_id.GetValue().replace(",", " ").split()
        for i in ids:
            self.jobs.put(("lcsc", i, False, dict(self._read_cfg())))
        self.lcsc_id.SetValue("")

    def _on_pick(self, evt):
        exts = "*.zip;*.kicad_sym;*.kicad_mod;*.lib;*.SchLib;*.PcbLib;*.IntLib"
        with wx.FileDialog(self, _("pick_title"),
                           wildcard="%s (%s)|%s|%s|*.*" % (_("wild_parts"), exts, exts, _("wild_all")),
                           style=wx.FD_OPEN | wx.FD_MULTIPLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._queue_files(dlg.GetPaths())

    def _queue_files(self, paths, auto=False):
        for p in paths:
            self.jobs.put(("file", p, auto, dict(self._read_cfg())))

    def _update_watch(self):
        c = self._read_cfg()
        if c["watch"] and os.path.isdir(c["watch_dir"]):
            if not self.watcher or self.watcher.folder != c["watch_dir"]:
                self.watcher = FolderWatcher(c["watch_dir"])
                self.log(_("watching", c["watch_dir"]))
            self.timer.Start(2000)
        else:
            self.timer.Stop()
            self.watcher = None

    def _on_timer(self, evt):
        if self.watcher:
            new = self.watcher.poll()
            if new:
                self._queue_files(new, auto=True)

    # --- worker thread -----------------------------------------------------
    def _worker(self):
        while True:
            job = self.jobs.get()
            if job is None:
                return
            try:
                kind, target, auto, cfg = job
                imp = self._importer(self.log, cfg)  # snapshot: geen wx-calls in deze thread
                if job[0] == "lcsc":
                    res = lcsc.fetch(job[1], imp, log=self.log)
                    label = job[1]
                else:
                    label = os.path.basename(job[1])
                    self.log("▶ %s" % label)
                    res = imp.import_path(job[1])
                for e in res.errors:
                    self.log("  ✖ %s" % e)
                if res.skipped:
                    self.log(_("skipped", ", ".join(res.skipped)))
                if res.symbols or res.footprints or res.models:
                    self.log("  ✔ %s: %s  [%s]" % (label, res.summary(), ", ".join(res.symbols or res.footprints)))
                    if job[0] == "file" and auto and cfg["delete_after_import"] and not res.errors:
                        try:
                            os.remove(job[1])
                        except OSError:
                            pass
            except Exception as e:
                self.log(_("unexpected", e))

    def _on_close(self, evt):
        global _instance
        config.save(self._read_cfg())
        self.timer.Stop()
        self.jobs.put(None)
        _instance = None
        evt.Skip()


def show(parent=None):
    """Eén venster tegelijk."""
    global _instance
    if _instance:
        _instance.Raise()
        return _instance
    _instance = PartDropDialog(parent)
    _instance.Show()
    return _instance
