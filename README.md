# PartDrop

KiCad 8 plugin die componenten uit allerlei bronnen in **één eigen library** zet:
symbool, footprint en 3D-model, meteen aan elkaar gekoppeld.

| Bron | Hoe |
|---|---|
| LCSC / JLCPCB / EasyEDA | C-nummer intypen (bv. `C2040`), via easyeda2kicad |
| SnapEDA, Ultra Librarian, Samacsys/Mouser, DigiKey, Octopart | ZIP slepen, kiezen of automatisch uit Downloads |
| Altium `.SchLib` / `.PcbLib` / `.IntLib` | Slepen; conversie via `kicad-cli` |
| Losse `.kicad_sym` / `.kicad_mod` / legacy `.lib` | Slepen |

## Wat het doet

- Alles komt in `<map>/<naam>.kicad_sym`, `<naam>.pretty/` en `<naam>.3dshapes/`.
- Het `Footprint`-veld van elk symbool wordt `<naam>:<footprint>`.
- 3D-paden in footprints wijzen naar `<naam>.3dshapes` (STEP krijgt voorrang, instelbaar).
  Ontbreekt een model in de footprint, dan wordt het toegevoegd als de naam overeenkomt.
- Velden worden genormaliseerd: `MPN`, `Manufacturer`, `LCSC` (uit varianten zoals
  `Manufacturer_Name`, `LCSC Part`, …). Zonder MPN wordt de symboolnaam gebruikt.
- **Registreer in KiCad** voegt de library toe aan de globale `sym-lib-table` en
  `fp-lib-table` (backup: `*.partdrop-backup`). Daarna één keer KiCad herstarten.
- **Map in het oog houden**: nieuwe ZIP's in bv. Downloads worden automatisch
  geïmporteerd zolang het venster open staat. ZIP's die al stonden en ZIP's zonder
  EDA-bestanden worden genegeerd.
- Bestaande onderdelen worden overgeslagen tenzij "Bestaande overschrijven" aan staat.
- Instellingen staan in `<KiCad-configmap>/partdrop.json` en overleven updates.

## Installeren

1. Download `PartDrop-x.y.z.zip` bij [Releases](https://github.com/Sepcode2/PartDrop/releases/latest).
   KiCad → **Plugin and Content Manager** → **Install from File…** → kies die ZIP
2. **Apply Pending Changes**, open de PCB Editor → knop in de toolbar
   (of **Tools → External Plugins → PartDrop**).
3. Kies naam + map, klik **Registreer in KiCad**, herstart KiCad.

LCSC-import installeert bij het eerste gebruik `easyeda2kicad` in de Python van KiCad
(`pip install --user`). Lukt dat niet, open dan de **KiCad Command Prompt** en voer
`pip install easyeda2kicad` uit.

## Gebruiken in de schema editor

KiCad 8 laat plugins enkel toe in de PCB editor. Klik daarom één keer op
**Snelkoppeling maken**: PartDrop komt dan op je bureaublad en in het Startmenu
en start los (met de Python van KiCad). Zet **Altijd bovenaan** aan om het venster
naast de schema editor te houden. Geïmporteerde symbolen verschijnen in
**Add Symbol** (`A`); zie je ze niet meteen, sluit en heropen dan de schema editor.

## Taal

PartDrop volgt automatisch de taal van KiCad (Nederlands, English, Deutsch, Français,
Español, Italiano; andere talen → English). Staat KiCad op *Default*, dan wordt de
systeemtaal gebruikt. Je kunt de taal ook vastzetten onderaan bij **Taal**.
Vertalingen staan in `plugins/i18n.py`.

## Structuur

```
plugins/
  __init__.py   ActionPlugin-registratie
  gui.py        wxPython venster, worker-thread, watcher-timer
  importer.py   ZIP/map → eigen library (kern)
  sexpr.py      S-expression parser/serializer
  lcsc.py       easyeda2kicad als subprocess
  libtable.py   sym-lib-table / fp-lib-table
  watcher.py    Downloads-map pollen
  kicad_env.py  paden, kicad-cli, python
  config.py     instellingen
  standalone.py PartDrop los starten (zonder PCB editor)
  shortcut.py   snelkoppeling bureaublad/Startmenu
  i18n.py       vertalingen en taaldetectie
metadata.json   PCM-manifest
```

## Ontwikkelen

```
python build.py                 # maakt dist/PartDrop-<versie>.zip
python tests/test_importer.py   # tests zonder KiCad
```

## Licentie

MIT. LCSC-import gebruikt [easyeda2kicad](https://github.com/uPesy/easyeda2kicad.py) (AGPL-3.0)
als apart proces; het wordt niet meegeleverd.

