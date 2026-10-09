"""Vertalingen. PartDrop volgt de taal van KiCad (of de systeemtaal als KiCad op 'Default' staat).

Een taal toevoegen: zet een code in LANGS en voeg op dezelfde plek in elke tuple een vertaling toe.
Ontbreekt een vertaling (None), dan wordt Engels gebruikt.
"""
import json
import os
import sys

LANGS = ("en", "nl", "de", "fr", "es", "it")
NAMES = {"en": "English", "nl": "Nederlands", "de": "Deutsch", "fr": "Français",
         "es": "Español", "it": "Italiano"}

T = {
    # --- venster ---
    "title": ("PartDrop – import components", "PartDrop – componenten importeren",
              "PartDrop – Bauteile importieren", "PartDrop – importer des composants",
              "PartDrop – importar componentes", "PartDrop – importa componenti"),
    "box_lib": ("Your library", "Jouw library", "Deine Bibliothek", "Votre bibliothèque",
                "Tu biblioteca", "La tua libreria"),
    "name": ("Name", "Naam", "Name", "Nom", "Nombre", "Nome"),
    "folder": ("Folder", "Map", "Ordner", "Dossier", "Carpeta", "Cartella"),
    "register": ("Register in KiCad", "Registreer in KiCad", "In KiCad registrieren",
                 "Enregistrer dans KiCad", "Registrar en KiCad", "Registra in KiCad"),
    "open_folder": ("Open folder", "Open map", "Ordner öffnen", "Ouvrir le dossier",
                    "Abrir carpeta", "Apri cartella"),
    "shortcut_btn": ("Create shortcut", "Snelkoppeling maken", "Verknüpfung erstellen",
                     "Créer un raccourci", "Crear acceso directo", "Crea collegamento"),
    "shortcut_tip": ("Puts PartDrop on your desktop and in the Start menu, so you can also open it next to the schematic editor",
                     "Zet PartDrop op je bureaublad en in het Startmenu, zodat je het ook naast de schema editor kan openen",
                     "Legt PartDrop auf den Desktop und ins Startmenü, damit du es auch neben dem Schaltplaneditor öffnen kannst",
                     "Place PartDrop sur le bureau et dans le menu Démarrer pour l'ouvrir aussi à côté de l'éditeur de schémas",
                     "Coloca PartDrop en el escritorio y en el menú Inicio para abrirlo también junto al editor de esquemas",
                     "Mette PartDrop sul desktop e nel menu Start, così puoi aprirlo anche accanto all'editor di schemi"),
    "box_lcsc": ("LCSC / JLCPCB part", "LCSC / JLCPCB onderdeel", "LCSC / JLCPCB Bauteil",
                 "Composant LCSC / JLCPCB", "Componente LCSC / JLCPCB", "Componente LCSC / JLCPCB"),
    "lcsc_hint": ("e.g. C2040 (separate multiple with spaces)", "bv. C2040 (meerdere scheiden met spatie)",
                  "z. B. C2040 (mehrere mit Leerzeichen trennen)", "ex. C2040 (séparer plusieurs par des espaces)",
                  "p. ej. C2040 (separa varios con espacios)", "es. C2040 (separa più codici con spazi)"),
    "import_btn": ("Import", "Importeer", "Importieren", "Importer", "Importar", "Importa"),
    "drop_text": ("Drop ZIPs, folders or .SchLib/.PcbLib files here\n(SnapEDA, Ultra Librarian, Samacsys, Mouser, DigiKey, Altium…)",
                  "Sleep ZIP's, mappen of .SchLib/.PcbLib hierheen\n(SnapEDA, Ultra Librarian, Samacsys, Mouser, DigiKey, Altium…)",
                  "ZIPs, Ordner oder .SchLib/.PcbLib hierher ziehen\n(SnapEDA, Ultra Librarian, Samacsys, Mouser, DigiKey, Altium…)",
                  "Déposez ici des ZIP, dossiers ou fichiers .SchLib/.PcbLib\n(SnapEDA, Ultra Librarian, Samacsys, Mouser, DigiKey, Altium…)",
                  "Arrastra aquí ZIP, carpetas o archivos .SchLib/.PcbLib\n(SnapEDA, Ultra Librarian, Samacsys, Mouser, DigiKey, Altium…)",
                  "Trascina qui ZIP, cartelle o file .SchLib/.PcbLib\n(SnapEDA, Ultra Librarian, Samacsys, Mouser, DigiKey, Altium…)"),
    "pick_btn": ("Or choose file(s)…", "Of kies bestand(en)…", "Oder Datei(en) wählen…",
                 "Ou choisir des fichiers…", "O elige archivo(s)…", "Oppure scegli file…"),
    "box_auto": ("Automatic and options", "Automatisch en opties", "Automatik und Optionen",
                 "Automatique et options", "Automático y opciones", "Automatico e opzioni"),
    "watch": ("Watch folder:", "Map in het oog houden:", "Ordner überwachen:", "Surveiller le dossier :",
              "Vigilar carpeta:", "Monitora cartella:"),
    "delete_after": ("Delete ZIP after import", "ZIP verwijderen na import", "ZIP nach Import löschen",
                     "Supprimer le ZIP après import", "Borrar ZIP tras importar", "Elimina ZIP dopo l'import"),
    "overwrite": ("Overwrite existing", "Bestaande overschrijven", "Vorhandene überschreiben",
                  "Écraser l'existant", "Sobrescribir existentes", "Sovrascrivi esistenti"),
    "prefer_step": ("Prefer STEP over WRL", "STEP verkiezen boven WRL", "STEP statt WRL bevorzugen",
                    "Préférer STEP à WRL", "Preferir STEP a WRL", "Preferisci STEP a WRL"),
    "on_top": ("Always on top", "Altijd bovenaan", "Immer im Vordergrund", "Toujours au premier plan",
               "Siempre visible", "Sempre in primo piano"),
    "language": ("Language:", "Taal:", "Sprache:", "Langue :", "Idioma:", "Lingua:"),
    "lang_auto": ("Automatic (KiCad)", "Automatisch (KiCad)", "Automatisch (KiCad)", "Automatique (KiCad)",
                  "Automático (KiCad)", "Automatico (KiCad)"),
    "lang_restart": ("Language changed. Close and reopen PartDrop to apply it.",
                     "Taal gewijzigd. Sluit PartDrop en open het opnieuw om dit toe te passen.",
                     "Sprache geändert. Schließe PartDrop und öffne es erneut.",
                     "Langue modifiée. Fermez et rouvrez PartDrop pour l'appliquer.",
                     "Idioma cambiado. Cierra y vuelve a abrir PartDrop para aplicarlo.",
                     "Lingua cambiata. Chiudi e riapri PartDrop per applicarla."),
    # --- log / meldingen in het venster ---
    "log_library": ("Library: %s", "Library: %s", "Bibliothek: %s", "Bibliothèque : %s",
                    "Biblioteca: %s", "Libreria: %s"),
    "cli_missing": ("not found (legacy/Altium conversion disabled)",
                    "niet gevonden (legacy/Altium conversie uitgeschakeld)",
                    "nicht gefunden (Legacy-/Altium-Konvertierung deaktiviert)",
                    "introuvable (conversion legacy/Altium désactivée)",
                    "no encontrado (conversión legacy/Altium desactivada)",
                    "non trovato (conversione legacy/Altium disattivata)"),
    "registered": ("✔ registered", "✔ geregistreerd", "✔ registriert", "✔ enregistrée",
                   "✔ registrada", "✔ registrata"),
    "not_registered": ("not registered yet", "nog niet geregistreerd", "noch nicht registriert",
                       "pas encore enregistrée", "aún no registrada", "non ancora registrata"),
    "reg_done": ("The library has been added to KiCad.\n\nRestart KiCad once so the symbols and footprints show up.\n\n"
                 "Tip: don't change anything in 'Manage Libraries' until that restart, or KiCad may overwrite the table.",
                 "De library is toegevoegd aan KiCad.\n\nHerstart KiCad één keer zodat de symbolen en footprints zichtbaar worden.\n\n"
                 "Tip: verander tot die herstart niets in 'Manage Libraries', anders kan KiCad de tabel overschrijven.",
                 "Die Bibliothek wurde zu KiCad hinzugefügt.\n\nStarte KiCad einmal neu, damit Symbole und Footprints erscheinen.\n\n"
                 "Tipp: Ändere bis zum Neustart nichts unter 'Bibliotheken verwalten', sonst kann KiCad die Tabelle überschreiben.",
                 "La bibliothèque a été ajoutée à KiCad.\n\nRedémarrez KiCad une fois pour voir les symboles et empreintes.\n\n"
                 "Astuce : ne modifiez rien dans 'Gérer les bibliothèques' avant ce redémarrage, sinon KiCad peut écraser la table.",
                 "La biblioteca se ha añadido a KiCad.\n\nReinicia KiCad una vez para que aparezcan los símbolos y huellas.\n\n"
                 "Consejo: no cambies nada en 'Gestionar bibliotecas' hasta reiniciar, o KiCad puede sobrescribir la tabla.",
                 "La libreria è stata aggiunta a KiCad.\n\nRiavvia KiCad una volta per vedere simboli e footprint.\n\n"
                 "Suggerimento: non modificare nulla in 'Gestisci librerie' prima del riavvio, altrimenti KiCad può sovrascrivere la tabella."),
    "reg_failed": ("Registration failed: %s", "Registreren mislukt: %s", "Registrierung fehlgeschlagen: %s",
                   "Échec de l'enregistrement : %s", "Error al registrar: %s", "Registrazione non riuscita: %s"),
    "shortcut_done": ("Shortcut created:\n\n%s\n\nThis lets you open PartDrop even when only the schematic editor is open. "
                      "Turn on 'Always on top' to keep the window next to it.",
                      "Snelkoppeling gemaakt:\n\n%s\n\nZo open je PartDrop ook als enkel de schema editor openstaat. "
                      "Zet 'Altijd bovenaan' aan om het venster ernaast te houden.",
                      "Verknüpfung erstellt:\n\n%s\n\nSo kannst du PartDrop auch öffnen, wenn nur der Schaltplaneditor offen ist. "
                      "Aktiviere 'Immer im Vordergrund', um das Fenster daneben zu halten.",
                      "Raccourci créé :\n\n%s\n\nVous pouvez ainsi ouvrir PartDrop même si seul l'éditeur de schémas est ouvert. "
                      "Activez 'Toujours au premier plan' pour garder la fenêtre à côté.",
                      "Acceso directo creado:\n\n%s\n\nAsí puedes abrir PartDrop aunque solo esté abierto el editor de esquemas. "
                      "Activa 'Siempre visible' para mantener la ventana al lado.",
                      "Collegamento creato:\n\n%s\n\nCosì puoi aprire PartDrop anche con solo l'editor di schemi aperto. "
                      "Attiva 'Sempre in primo piano' per tenere la finestra accanto."),
    "pick_title": ("Choose component files", "Kies component-bestanden", "Bauteildateien wählen",
                   "Choisir des fichiers de composants", "Elegir archivos de componentes", "Scegli file dei componenti"),
    "wild_parts": ("Components", "Componenten", "Bauteile", "Composants", "Componentes", "Componenti"),
    "wild_all": ("All files", "Alle bestanden", "Alle Dateien", "Tous les fichiers", "Todos los archivos", "Tutti i file"),
    "watching": ("Watching for new ZIPs in %s", "Ik let op nieuwe ZIP's in %s", "Überwache neue ZIPs in %s",
                 "Surveillance des nouveaux ZIP dans %s", "Vigilando ZIP nuevos en %s", "Monitoraggio nuovi ZIP in %s"),
    "skipped": ("  ↷ skipped (already exists): %s", "  ↷ overgeslagen (bestaat al): %s",
                "  ↷ übersprungen (existiert bereits): %s", "  ↷ ignoré (existe déjà) : %s",
                "  ↷ omitido (ya existe): %s", "  ↷ saltato (esiste già): %s"),
    "unexpected": ("  ✖ unexpected error: %s", "  ✖ onverwachte fout: %s", "  ✖ unerwarteter Fehler: %s",
                   "  ✖ erreur inattendue : %s", "  ✖ error inesperado: %s", "  ✖ errore imprevisto: %s"),
    "n_symbols": ("%d symbol(s)", "%d symbool(en)", "%d Symbol(e)", "%d symbole(s)", "%d símbolo(s)", "%d simbolo/i"),
    "n_footprints": ("%d footprint(s)", "%d footprint(s)", "%d Footprint(s)", "%d empreinte(s)",
                     "%d huella(s)", "%d footprint"),
    "n_models": ("%d 3D model(s)", "%d 3D-model(len)", "%d 3D-Modell(e)", "%d modèle(s) 3D",
                 "%d modelo(s) 3D", "%d modello/i 3D"),
    "nothing": ("nothing", "niets", "nichts", "rien", "nada", "niente"),
    # --- importer ---
    "file_missing": ("File does not exist: %s", "Bestand bestaat niet: %s", "Datei existiert nicht: %s",
                     "Le fichier n'existe pas : %s", "El archivo no existe: %s", "Il file non esiste: %s"),
    "altium_sym": ("Altium symbol library found, converting with kicad-cli…",
                   "Altium symboolbibliotheek gevonden, converteren met kicad-cli…",
                   "Altium-Symbolbibliothek gefunden, Konvertierung mit kicad-cli…",
                   "Bibliothèque de symboles Altium trouvée, conversion avec kicad-cli…",
                   "Biblioteca de símbolos Altium encontrada, convirtiendo con kicad-cli…",
                   "Libreria simboli Altium trovata, conversione con kicad-cli…"),
    "altium_fp": ("Altium footprint library found, converting…", "Altium footprintbibliotheek gevonden, converteren…",
                  "Altium-Footprintbibliothek gefunden, Konvertierung…",
                  "Bibliothèque d'empreintes Altium trouvée, conversion…",
                  "Biblioteca de huellas Altium encontrada, convirtiendo…",
                  "Libreria footprint Altium trovata, conversione…"),
    "needs_cli": ("This package needs kicad-cli for conversion (not found)",
                  "Dit pakket heeft kicad-cli nodig voor conversie (niet gevonden)",
                  "Dieses Paket benötigt kicad-cli zur Konvertierung (nicht gefunden)",
                  "Ce paquet nécessite kicad-cli pour la conversion (introuvable)",
                  "Este paquete necesita kicad-cli para la conversión (no encontrado)",
                  "Questo pacchetto richiede kicad-cli per la conversione (non trovato)"),
    "nothing_usable": ("No usable KiCad/Altium files found in the package",
                       "Geen bruikbare KiCad/Altium bestanden gevonden in het pakket",
                       "Keine verwendbaren KiCad-/Altium-Dateien im Paket gefunden",
                       "Aucun fichier KiCad/Altium utilisable dans le paquet",
                       "No se encontraron archivos KiCad/Altium utilizables en el paquete",
                       "Nessun file KiCad/Altium utilizzabile nel pacchetto"),
    "cli_cant_convert": ("kicad-cli not found: cannot convert %s", "kicad-cli niet gevonden: kan %s niet converteren",
                         "kicad-cli nicht gefunden: %s kann nicht konvertiert werden",
                         "kicad-cli introuvable : impossible de convertir %s",
                         "kicad-cli no encontrado: no se puede convertir %s",
                         "kicad-cli non trovato: impossibile convertire %s"),
    "sym_upgrade_failed": ("kicad-cli sym upgrade failed for %s: %s", "kicad-cli sym upgrade faalde voor %s: %s",
                           "kicad-cli sym upgrade fehlgeschlagen für %s: %s", "échec de kicad-cli sym upgrade pour %s : %s",
                           "kicad-cli sym upgrade falló para %s: %s", "kicad-cli sym upgrade non riuscito per %s: %s"),
    "fp_upgrade_failed": ("kicad-cli fp upgrade failed: %s", "kicad-cli fp upgrade faalde: %s",
                          "kicad-cli fp upgrade fehlgeschlagen: %s", "échec de kicad-cli fp upgrade : %s",
                          "kicad-cli fp upgrade falló: %s", "kicad-cli fp upgrade non riuscito: %s"),
    "altium_fp_failed": ("Altium footprint conversion failed: %s", "Altium footprint conversie mislukt: %s",
                         "Altium-Footprint-Konvertierung fehlgeschlagen: %s", "Échec de la conversion d'empreinte Altium : %s",
                         "Error en la conversión de huellas Altium: %s", "Conversione footprint Altium non riuscita: %s"),
    "fp_unreadable": ("Footprint %s unreadable: %s", "Footprint %s onleesbaar: %s", "Footprint %s nicht lesbar: %s",
                      "Empreinte %s illisible : %s", "Huella %s ilegible: %s", "Footprint %s illeggibile: %s"),
    "sym_unreadable": ("Symbol file unreadable: %s", "Symboolbestand onleesbaar: %s", "Symboldatei nicht lesbar: %s",
                       "Fichier de symboles illisible : %s", "Archivo de símbolos ilegible: %s", "File simboli illeggibile: %s"),
    # --- LCSC ---
    "installing": ("Installing easyeda2kicad into KiCad's Python…", "easyeda2kicad installeren in de Python van KiCad…",
                   "Installiere easyeda2kicad in KiCads Python…", "Installation d'easyeda2kicad dans le Python de KiCad…",
                   "Instalando easyeda2kicad en el Python de KiCad…", "Installazione di easyeda2kicad nel Python di KiCad…"),
    "invalid_lcsc": ("Invalid LCSC number: %r (expected e.g. C2040)", "Ongeldig LCSC-nummer: %r (verwacht bv. C2040)",
                     "Ungültige LCSC-Nummer: %r (erwartet z. B. C2040)", "Numéro LCSC invalide : %r (attendu ex. C2040)",
                     "Número LCSC no válido: %r (se espera p. ej. C2040)", "Codice LCSC non valido: %r (atteso es. C2040)"),
    "no_python": ("KiCad's Python not found", "Python van KiCad niet gevonden", "KiCads Python nicht gefunden",
                  "Python de KiCad introuvable", "No se encontró el Python de KiCad", "Python di KiCad non trovato"),
    "install_failed": ("easyeda2kicad could not be installed (try: pip install easyeda2kicad in the KiCad Command Prompt)",
                       "easyeda2kicad kon niet geïnstalleerd worden (probeer: pip install easyeda2kicad in de KiCad Command Prompt)",
                       "easyeda2kicad konnte nicht installiert werden (versuche: pip install easyeda2kicad in der KiCad-Eingabeaufforderung)",
                       "easyeda2kicad n'a pas pu être installé (essayez : pip install easyeda2kicad dans l'invite de commandes KiCad)",
                       "No se pudo instalar easyeda2kicad (prueba: pip install easyeda2kicad en el símbolo del sistema de KiCad)",
                       "Impossibile installare easyeda2kicad (prova: pip install easyeda2kicad nel prompt dei comandi di KiCad)"),
    "fetching": ("Fetching %s from EasyEDA…", "%s ophalen bij EasyEDA…", "Lade %s von EasyEDA…",
                 "Récupération de %s depuis EasyEDA…", "Descargando %s de EasyEDA…", "Scaricamento di %s da EasyEDA…"),
    "e2k_empty": ("easyeda2kicad returned nothing:\n%s", "easyeda2kicad gaf niets terug:\n%s",
                  "easyeda2kicad lieferte nichts:\n%s", "easyeda2kicad n'a rien renvoyé :\n%s",
                  "easyeda2kicad no devolvió nada:\n%s", "easyeda2kicad non ha restituito nulla:\n%s"),
    "e2k_error": ("easyeda2kicad reported an error, trying what is there:\n%s",
                  "easyeda2kicad meldde een fout, ik probeer wat er wel is:\n%s",
                  "easyeda2kicad meldete einen Fehler, versuche das Vorhandene:\n%s",
                  "easyeda2kicad a signalé une erreur, essai avec ce qui existe :\n%s",
                  "easyeda2kicad informó un error, probando con lo disponible:\n%s",
                  "easyeda2kicad ha segnalato un errore, provo con ciò che c'è:\n%s"),
    # --- lib-tables / snelkoppeling ---
    "table_present": ("%s: '%s' is already registered.", "%s: '%s' staat al in KiCad.",
                      "%s: '%s' ist bereits registriert.", "%s : '%s' est déjà enregistrée.",
                      "%s: '%s' ya está registrada.", "%s: '%s' è già registrata."),
    "table_added": ("%s: '%s' added (%s)", "%s: '%s' toegevoegd (%s)", "%s: '%s' hinzugefügt (%s)",
                    "%s : '%s' ajoutée (%s)", "%s: '%s' añadida (%s)", "%s: '%s' aggiunta (%s)"),
    "table_updated": ("%s: '%s' updated (%s)", "%s: '%s' bijgewerkt (%s)", "%s: '%s' aktualisiert (%s)",
                      "%s : '%s' mise à jour (%s)", "%s: '%s' actualizada (%s)", "%s: '%s' aggiornata (%s)"),
    "lib_descr": ("Own components (PartDrop)", "Eigen componenten (PartDrop)", "Eigene Bauteile (PartDrop)",
                  "Composants personnels (PartDrop)", "Componentes propios (PartDrop)", "Componenti personali (PartDrop)"),
    "shortcut_failed": ("Creating shortcut failed: %s", "Snelkoppeling maken mislukt: %s",
                        "Verknüpfung erstellen fehlgeschlagen: %s", "Échec de création du raccourci : %s",
                        "Error al crear el acceso directo: %s", "Creazione collegamento non riuscita: %s"),
    "shortcut_log": ("Shortcut: %s", "Snelkoppeling: %s", "Verknüpfung: %s", "Raccourci : %s",
                     "Acceso directo: %s", "Collegamento: %s"),
}

_lang = None


def _match(text):
    """'Nederlands', 'Dutch', 'nl_BE', 'German', 'Deutsch'… → taalcode of None."""
    t = (text or "").strip().lower()
    if not t or t == "default" or not t[0].isalpha():
        return None
    prefixes = {"nl": ("nl", "ned", "dut", "vla", "flem"), "en": ("en",), "de": ("de", "ger"),
                "fr": ("fr",), "es": ("es", "spa"), "it": ("it",)}
    for code, pre in prefixes.items():
        if t.startswith(pre):
            return code
    return "en"  # wel een taal gekozen, maar niet vertaald → Engels


def kicad_language():
    """Taalcode zoals ingesteld in KiCad, of None bij 'Default'."""
    from . import kicad_env
    try:
        with open(os.path.join(kicad_env.config_dir(), "kicad_common.json"), encoding="utf-8") as f:
            return _match(json.load(f).get("system", {}).get("language"))
    except (OSError, ValueError, AttributeError):
        return None


def system_language():
    try:  # binnen KiCad: de locale die KiCad zelf heeft gezet
        import wx
        loc = wx.GetLocale()
        if loc:
            return _match(loc.GetCanonicalName())
        return _match(wx.Locale.GetLanguageCanonicalName(wx.Locale.GetSystemLanguage()))
    except Exception:
        pass
    import locale
    try:
        return _match(locale.getlocale()[0] or os.environ.get("LANG", ""))
    except Exception:
        return None


def detect(override="auto"):
    if override and override != "auto" and override in LANGS:
        return override
    inside_kicad = "pcbnew" in sys.modules and not os.environ.get("PARTDROP_STANDALONE")
    if inside_kicad:  # KiCad heeft zijn eigen taal al als wx-locale gezet
        return system_language() or kicad_language() or "en"
    return kicad_language() or system_language() or "en"


def set_language(code):
    global _lang
    _lang = code if code in LANGS else "en"


def current():
    if _lang is None:
        set_language(detect())
    return _lang


def _(key, *args):
    row = T.get(key)
    if row is None:
        text = key
    else:
        text = row[LANGS.index(current())] or row[0]
    return text % args if args else text
