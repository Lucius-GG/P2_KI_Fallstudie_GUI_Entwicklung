from Manager import TaskManager
from datetime import datetime
from typing import List


class PlannerController:
    """
    Leichte Brücke zwischen GUI und Manager.
    Bietet einen stabilen API für die GUI-Komponenten.
    """

    # ===== INITIALISIERUNG =====
    # Erstellt den Controller und initialisiert den TaskManager
    def __init__(self, view=None, storage_path: str = None):
        self.view = view
        self.manager = TaskManager(storage_path)

    # ===== DEMO-DATEN =====
    # Lädt Beispiel-Aufgaben in den Manager
    def load_demo_data(self):
        self.manager.aufgaben.clear()
        self.manager.geloescht.clear()
        self.manager._next_id = 1
        
        self.manager.add_task(
            "GUI Refinement",
            "Logo auf Vektor-Basis umgestellt",
            prio=5,
            faellig=datetime.fromisoformat("2026-05-24"),
            status="in_bearbeitung"
        )
        
        self.manager.add_task(
            "KI Fallstudie",
            "Integration der ToDoListeKlassen",
            prio=3,
            faellig=datetime.fromisoformat("2026-05-29"),
            status="offen"
        )
        
        self.manager.add_task(
            "DPI Bugfix",
            "High-DPI Awareness für Windows 11",
            prio=1,
            faellig=datetime.fromisoformat("2026-05-22"),
            status="erledigt"
        )
        
        self.manager.add_task(
            "Testing",
            "Unit Tests für Manager schreiben",
            prio=3,
            faellig=datetime.fromisoformat("2026-06-01"),
            status="offen"
        )
        
        self.manager.add_task(
            "hhdd",
            "dd",
            prio=3,
            faellig=datetime.fromisoformat("2026-05-22"),
            status="offen"
        )

        self.manager.speichere_daten()

    # ===== TASK-ABFRAGEN =====
    # Ruft Tasks nach verschiedenen Kriterien ab
    def get_tasks_by_status(self, status: str):
        """Gibt alle Tasks mit einem bestimmten Status zurück"""
        return self.manager.get_tasks_by_status(status)

    def get_task(self, task_id: str):
        """Gibt eine einzelne Task nach ID zurück"""
        return self.manager.get_task(task_id)

    def get_all_tasks(self) -> List:
        """Gibt alle Tasks als Liste zurück"""
        return list(self.manager.aufgaben.values())

    # ===== SUCHE =====
    # Sucht nach Tasks basierend auf Titel und Beschreibung
    def search_tasks(self, query: str):
        """Sucht Tasks nach Titel und Beschreibung"""
        q = (query or "").strip().lower()
        
        if not q:
            return self.get_all_tasks()
        
        out = []
        for t in self.get_all_tasks():
            titel = getattr(t, "get_titel", lambda: "")()
            besch = getattr(t, "get_beschreibung", lambda: "")() or ""
            
            if q in titel.lower() or q in besch.lower():
                out.append(t)
        
        return out

    # ===== ÜBERFÄLLIGE TASKS =====
    # Zählt Tasks die überfällig sind
    def get_overdue_count(self) -> int:
        """Zählt alle überfälligen Tasks (offen/in_bearbeitung)"""
        today = datetime.now().date()
        c = 0
        
        for status in ("offen", "in_bearbeitung"):
            for t in self.get_tasks_by_status(status):
                fd = getattr(t, "get_faelligkeitsdatum", lambda: None)()
                
                if fd and fd.date() < today:
                    c += 1
        
        return c

    # ===== TASK-VERWALTUNG =====
    # Erstellt, löscht und ändert Tasks
    def add_task(
        self,
        titel: str,
        beschreibung: str = "",
        prio: int = 3,
        faellig: datetime = None
    ):
        """Erstellt eine neue Task mit Status 'offen'"""
        return self.manager.add_task(
            titel,
            beschreibung,
            prio,
            faellig,
            status="offen"
        )

    def delete_task(self, task_id: str):
        """Löscht eine Task aus dem Manager"""
        return self.manager.aufgabe_entfernen(task_id)

    def complete_task(self, task_id: str):
        """Markiert eine Task als erledigt"""
        return self.manager.complete_task(task_id)

    def bearbeitung_task(self, task_id: str):
        """Setzt eine Task auf Status 'in_bearbeitung'"""
        return self.manager.bearbeitung_task(task_id)

    def move_task(self, task_id: str, target_status: str):
        """Verschiebt eine Task zu einem anderen Status"""
        return self.manager.move_task(task_id, target_status)

    # ===== LÖSCHEN ALLER TASKS =====
    # Leert den kompletten Task-Manager
    def clear_all_tasks(self):
        """Löscht alle Tasks und setzt den Manager zurück"""
        self.manager.aufgaben.clear()
        self.manager.geloescht.clear()
        self.manager._next_id = 1
        self.manager.speichere_daten()

    # ===== SPEICHERN =====
    # Speichert alle Daten in der Datei
    def save(self):
        """Speichert alle Tasks in die JSON-Datei"""
        return self.manager.speichere_daten()

    # ===== RÜCKWÄRTS-KOMPATIBILITÄT =====
    # Unterstützt alte GUI-Methodennamen
    def speichere_daten(self):
        """Speichert alle Tasks (alte GUI-Methode)"""
        return self.save()