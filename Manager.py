# =====================
# Modul: Manager
# =====================

import json
from datetime import datetime
import ToDoListeKlassen as x

DATEI = "daten.json"


class AufgabenManager:

    def __init__(self):
        self.aufgaben = {}
        self.geloescht = {}
        self.lade_daten()

    # ---------------------
    # JSON speichern
    # ---------------------

    def speichere_daten(self):
        daten = {
            "aufgaben": [self.obj_to_dict(a) for a in self.aufgaben.values()],
            "geloescht": [self.obj_to_dict(a) for a in self.geloescht.values()]
        }

        with open(DATEI, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=4, ensure_ascii=False)

    # ---------------------
    # JSON laden
    # ---------------------

    def lade_daten(self):
        try:
            with open(DATEI, "r", encoding="utf-8") as f:
                daten = json.load(f)

            self.aufgaben = {
                int(a["id"]): self.dict_to_obj(a)
                for a in daten.get("aufgaben", [])
            }

            self.geloescht = {
                int(a["id"]): self.dict_to_obj(a)
                for a in daten.get("geloescht", [])
            }

        except FileNotFoundError:
            self.aufgaben = {}
            self.geloescht = {}

        except json.JSONDecodeError:
            print("Fehler: daten.json ist leer oder beschädigt.")
            self.aufgaben = {}
            self.geloescht = {}

    # ---------------------
    # Objekt zu Dictionary
    # ---------------------

    def obj_to_dict(self, a):
        return {
            "id": a.get_id(),
            "titel": a.get_titel(),
            "beschreibung": a.get_beschreibung(),
            "status": a.get_status(),

            "prio": a.get_prio()
            if hasattr(a, "get_prio")
            else None,

            "faelligkeit": a.get_faelligkeitsdatum().strftime("%Y-%m-%d")
            if hasattr(a, "get_faelligkeitsdatum") and a.get_faelligkeitsdatum()
            else None,

            "verbleibend": a.get_verbleibend()
            if hasattr(a, "get_verbleibend")
            else None,

            "wiederholung": a.get_wiederholung()
            if hasattr(a, "get_wiederholung")
            else False,

            "wiederholung_intervall": a.get_wiederholung_intervall()
            if hasattr(a, "get_wiederholung_intervall")
            else None
        }

    # ---------------------
    # Dictionary zu Objekt
    # ---------------------

    def dict_to_obj(self, d):

        if d.get("faelligkeit") is not None or d.get("prio") is not None:
            datum = None
            if d.get("faelligkeit"):
                try:
                    datum = datetime.strptime(d["faelligkeit"], "%Y-%m-%d")
                except ValueError:
                    datum = None

            aufgabe = x.TerminierteAufgabe(
                d["id"],
                d["titel"],
                d["beschreibung"],
                d.get("status", "offen"),
                d.get("prio", 1),
                datum,
                d.get("wiederholung", False),
                d.get("wiederholung_intervall", None)
            )

        else:
            aufgabe = x.EinfacheAufgabe(
                d["id"],
                d["titel"],
                d["beschreibung"],
                d.get("status", "offen")
            )

        return aufgabe

    # ---------------------
    # Aufgaben-Funktionen
    # ---------------------

    def aufgabe_hinzufuegen(self, aufgabe):
        self.aufgaben[aufgabe.get_id()] = aufgabe
        self.speichere_daten()

    def aufgabe_entfernen(self, id):
        if id in self.aufgaben:
            self.geloescht[id] = self.aufgaben.pop(id)
            self.speichere_daten()

    def aufgabe_wiederherstellen(self, id):
        if id in self.geloescht:
            self.aufgaben[id] = self.geloescht.pop(id)
            self.speichere_daten()

    def erledigt_setzen(self, id):
        if id in self.aufgaben:
            self.aufgaben[id].set_status("erledigt")
            self.speichere_daten()
        else:
            print(f"Aufgabe {id} existiert nicht.")

    def bearbeitung_setzen(self, id):
        """Setzt Aufgabe auf 'in_bearbeitung'"""
        if id in self.aufgaben:
            self.aufgaben[id].set_status("in_bearbeitung")
            self.speichere_daten()
        else:
            print(f"Aufgabe {id} existiert nicht.")

    def prioritaet_setzen(self, id, prioritaet):
        if id in self.aufgaben and hasattr(self.aufgaben[id], "set_prio"):
            try:
                prio_int = int(prioritaet)
                self.aufgaben[id].set_prio(prio_int)
                self.speichere_daten()
            except ValueError:
                print("Ungültige Priorität - nicht gesetzt.")

    def faelligkeit_setzen(self, id, datum):
        if id in self.aufgaben and hasattr(self.aufgaben[id], "set_faelligkeitsdatum"):
            self.aufgaben[id].set_faelligkeitsdatum(datum)
            self.speichere_daten()

    def alle_anzeigen(self):
        return [str(a) for a in self.aufgaben.values()]

    def nach_prioritaet_filtern(self, prioritaet):
        return [
            a
            for a in self.aufgaben.values()
            if hasattr(a, "get_prio") and a.get_prio() == prioritaet
        ]

    def nach_status_filtern(self, status):
        """Filtert Aufgaben nach Status"""
        return [a for a in self.aufgaben.values() if a.get_status() == status]

    def suche(self, suchwort):
        return [
            a
            for a in self.aufgaben.values()
            if suchwort.lower() in a.get_titel().lower()
            or suchwort.lower() in (a.get_beschreibung() or "").lower()
        ]