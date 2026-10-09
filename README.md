# PartDrop

A KiCad 8 plugin that imports components from all the usual sources into **one library of your own**:
symbol, footprint and 3D model, linked together and ready to use.

| Source | How |
|---|---|
| LCSC / JLCPCB / EasyEDA | Type a part number (e.g. `C2040`), fetched via easyeda2kicad |
| SnapEDA, Ultra Librarian, Samacsys/Mouser, DigiKey, Octopart | Drag in the ZIP, pick it, or let PartDrop grab it from Downloads |
| Altium `.SchLib` / `.PcbLib` / `.IntLib` | Drag in; converted with `kicad-cli` |
| Loose `.kicad_sym` / `.kicad_mod` / legacy `.lib` files | Drag in |

## Features

- Everything lands in `<folder>/<name>.kicad_sym`, `<name>.pretty/` and `<name>.3dshapes/`.
- Each symbol's `Footprint` field is set to `<name>:<footprint>`.
- 3D model paths in footprints point to `<name>.3dshapes` (STEP preferred over WRL, configurable).
  If a footprint has no model, one is added when the file name matches.
- Fields are normalized: `MPN`, `Manufacturer` and `LCSC` are filled in from common variants
  such as `Manufacturer_Name` or `LCSC Part`. Without an MPN, the symbol name is used.
- **Register in KiCad** adds the library to the global `sym-lib-table` and `fp-lib-table`
  (with a `*.partdrop-backup` copy). Restart KiCad once afterwards.
- **Watch folder**: new component ZIPs in e.g. Downloads are imported automatically while the
  window is open. ZIPs that were already there, and ZIPs without EDA files, are ignored.
- Existing parts are skipped unless **Overwrite existing** is enabled.
- Settings are stored in `<KiCad config folder>/partdrop.json` and survive plugin updates.

## Installation

1. Download `PartDrop-x.y.z.zip` from [Releases](https://github.com/Sepcode2/PartDrop/releases/latest).
   Use that file, not "Source code (zip)", which KiCad cannot install.
2. KiCad → **Plugin and Content Manager** → **Install from File…** → choose the ZIP →
   **Apply Pending Changes**.
3. Open the PCB Editor and click the PartDrop button in the toolbar
   (or **Tools → External Plugins → PartDrop**).
4. Choose a name and folder, click **Register in KiCad**, then restart KiCad.

The first LCSC import installs `easyeda2kicad` into KiCad's Python (`pip install --user`).
If that fails, open the **KiCad Command Prompt** and run `pip install easyeda2kicad`.

## Using it with the schematic editor

KiCad 8 only supports plugins in the PCB Editor. Click **Create shortcut** once: PartDrop is then
added to your desktop and Start menu and runs on its own, using KiCad's Python. Turn on
**Always on top** to keep the window next to the schematic editor. Imported symbols show up in
**Add Symbol** (`A`); if a new one is missing, close and reopen the schematic editor.

## Language

PartDrop follows KiCad's language (English, Nederlands, Deutsch, Français, Español, Italiano;
other languages fall back to English). If KiCad is set to *Default*, the system language is used.
You can also pick a fixed language under **Language** at the bottom of the window.
Translations live in `plugins/i18n.py`; new languages are welcome.

## Project layout

```
plugins/
  __init__.py   ActionPlugin registration
  gui.py        wxPython window, worker thread, watch-folder timer
  importer.py   ZIP/folder → your own library (core logic)
  sexpr.py      S-expression parser/serializer
  lcsc.py       easyeda2kicad as a subprocess
  libtable.py   sym-lib-table / fp-lib-table
  watcher.py    watch-folder polling
  kicad_env.py  paths, kicad-cli, Python
  config.py     settings
  standalone.py run PartDrop without the PCB Editor
  shortcut.py   desktop / Start menu shortcut
  i18n.py       translations and language detection
metadata.json   PCM manifest
```

## Development

```
python build.py                 # creates dist/PartDrop-<version>.zip
python tests/test_importer.py   # tests, no KiCad needed
```

To release: bump the version in `metadata.json`, push, then go to
**Actions → Release → Run workflow**. The workflow runs the tests, builds the ZIP and publishes
the GitHub release.

## License

MIT. LCSC import uses [easyeda2kicad](https://github.com/uPesy/easyeda2kicad.py) (AGPL-3.0)
as a separate process; it is not bundled.


