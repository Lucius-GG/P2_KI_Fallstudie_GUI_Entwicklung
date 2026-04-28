# =====================
# Modul: Manager
# =====================

import ToDoListeKlassen as x
#from datetime import datetime

class AufgabenManager:

    def __init__(self):
        self.aufgaben = {}
        self.geloescht = {}

    def aufgabe_hinzufuegen(self, aufgabe):
        self.aufgaben[aufgabe.get_id()] = aufgabe

    def aufgabe_entfernen(self, id):
        if id in self.aufgaben:
            self.geloescht[id] = self.aufgaben.pop(id)

    def aufgabe_wiederherstellen(self, id):
        if id in self.geloescht:
            self.aufgaben[id] = self.geloescht.pop(id)

    def erledigt_setzen(self, id):
        if id in self.aufgaben:
            self.aufgaben[id].set_status("erledigt")
        else:
            print(f"Aufgabe {id} existiert nicht.")

    def prioritaet_setzen(self, id, prioritaet):
        if id in self.aufgaben and hasattr(self.aufgaben[id], "set_prio"):
            try:
                prio_int = int(prioritaet)
                self.aufgaben[id].set_prio(prio_int)
            except ValueError:
                print("UngÃ¼ltige PrioritÃ¤t - nicht gesetzt.")


    def faelligkeit_setzen(self, id, datum):
        if id in self.aufgaben and hasattr(self.aufgaben[id], "set_faelligkeitsdatum"):
            self.aufgaben[id].set_faelligkeitsdatum(datum)

    def alle_anzeigen(self):
        return [str(a) for a in self.aufgaben.values()]

    def nach_prioritaet_filtern(self, prioritaet):
        return [str(a) for a in self.aufgaben.values() if hasattr(a, "get_prio") and a.get_prio() == prioritaet]

    def suche(self, suchwort):
        return [str(a) for a in self.aufgaben.values() if suchwort.lower() in a.get_titel().lower() or suchwort.lower() in a.get_beschreibung().lower()]
