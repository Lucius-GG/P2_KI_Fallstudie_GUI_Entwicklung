# =====================
# Modul: Manager
# =====================

import ToDoListeKlassen as klassen


class AufgabenManager:
    """
    Verwaltet alle Aufgaben und gelöschten Aufgaben.
    Stellt Methoden für Verwaltung, Filterung und Suche bereit.
    """
    
    def __init__(self):
        self.aufgaben = {}      # {id: aufgabe}
        self.geloescht = {}     # {id: aufgabe} - gelöschte Aufgaben

    def aufgabe_hinzufuegen(self, aufgabe):
        """Fügt eine Aufgabe zur Verwaltung hinzu"""
        self.aufgaben[aufgabe.get_id()] = aufgabe

    def aufgabe_entfernen(self, id):
        """Entfernt eine Aufgabe und speichert sie in geloescht"""
        if id in self.aufgaben:
            self.geloescht[id] = self.aufgaben.pop(id)
            return True
        return False

    def aufgabe_wiederherstellen(self, id):
        """Stellt eine gelöschte Aufgabe wieder her"""
        if id in self.geloescht:
            self.aufgaben[id] = self.geloescht.pop(id)
            return True
        return False

    def erledigt_setzen(self, id):
        """Markiert eine Aufgabe als erledigt"""
        if id in self.aufgaben:
            self.aufgaben[id].set_status("erledigt")
            return True
        return False

    def prioritaet_setzen(self, id, prioritaet):
        """Setzt die Priorität einer Aufgabe"""
        if id in self.aufgaben and hasattr(self.aufgaben[id], "set_prio"):
            try:
                prio_int = int(prioritaet)
                self.aufgaben[id].set_prio(prio_int)
                return True
            except ValueError:
                print("Ungültige Priorität - nicht gesetzt.")
                return False
        return False

    def faelligkeit_setzen(self, id, datum):
        """Setzt das Fälligkeitsdatum einer Aufgabe"""
        if id in self.aufgaben and hasattr(self.aufgaben[id], "set_faelligkeitsdatum"):
            self.aufgaben[id].set_faelligkeitsdatum(datum)
            return True
        return False

    def alle_anzeigen(self):
        """Gibt alle Aufgaben als Strings zurück"""
        return [str(a) for a in self.aufgaben.values()]

    def nach_prioritaet_filtern(self, prioritaet):
        """Filtert Aufgaben nach Priorität"""
        return [a for a in self.aufgaben.values() 
                if hasattr(a, "get_prio") and a.get_prio() == prioritaet]

    def nach_status_filtern(self, status: str):
        """Filtert Aufgaben nach Status"""
        return [a for a in self.aufgaben.values() if a.get_status() == status]

    def suche(self, suchwort):
        """Sucht nach Aufgaben mit Stichwort im Titel oder Beschreibung"""
        return [a for a in self.aufgaben.values() 
                if suchwort.lower() in a.get_titel().lower() or 
                   suchwort.lower() in a.get_beschreibung().lower()]

    def get_aufgabe(self, id):
        """Gibt eine spezifische Aufgabe zurück"""
        return self.aufgaben.get(id, None)
