from Manager import TaskManager
from datetime import datetime
from typing import List

class PlannerController:
    """Leichte Brücke GUI <-> Manager. Bietet stabilen API für GUI."""
    def __init__(self, view=None, storage_path: str = None):
        self.view = view
        self.manager = TaskManager(storage_path)

    def load_demo_data(self):
        # Leerer manager, dann Beispielaufgaben erzeugen
        self.manager.aufgaben.clear()
        self.manager.geloescht.clear()
        self.manager._next_id = 1
        self.manager.add_task("GUI Refinement", "Logo auf Vektor-Basis umgestellt", prio=5, faellig=datetime.fromisoformat("2026-05-24"), status="in_bearbeitung")
        self.manager.add_task("KI Fallstudie", "Integration der ToDoListeKlassen", prio=3, faellig=datetime.fromisoformat("2026-05-29"), status="offen")
        self.manager.add_task("DPI Bugfix", "High-DPI Awareness für Windows 11", prio=1, faellig=datetime.fromisoformat("2026-05-22"), status="erledigt")
        self.manager.add_task("Testing", "Unit Tests für Manager schreiben", prio=3, faellig=datetime.fromisoformat("2026-06-01"), status="offen")
        self.manager.add_task("hhdd", "dd", prio=3, faellig=datetime.fromisoformat("2026-05-22"), status="offen")

        self.manager.speichere_daten()

    def get_tasks_by_status(self, status: str):
        return self.manager.get_tasks_by_status(status)

    def get_task(self, task_id: str):
        return self.manager.get_task(task_id)

    def get_all_tasks(self) -> List:
        return list(self.manager.aufgaben.values())

    def search_tasks(self, query: str):
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

    def get_overdue_count(self) -> int:
        today = datetime.now().date()
        c = 0
        for status in ("offen", "in_bearbeitung"):
            for t in self.get_tasks_by_status(status):
                fd = getattr(t, "get_faelligkeitsdatum", lambda: None)()
                if fd and fd.date() < today:
                    c += 1
        return c

    def add_task(self, titel: str, beschreibung: str = "", prio: int = 3, faellig: datetime = None):
        return self.manager.add_task(titel, beschreibung, prio, faellig, status="offen")

    def delete_task(self, task_id: str):
        return self.manager.aufgabe_entfernen(task_id)

    def complete_task(self, task_id: str):
        return self.manager.complete_task(task_id)

    def bearbeitung_task(self, task_id: str):
        return self.manager.bearbeitung_task(task_id)

    def move_task(self, task_id: str, target_status: str):
        return self.manager.move_task(task_id, target_status)

    def clear_all_tasks(self):
        self.manager.aufgaben.clear()
        self.manager.geloescht.clear()
        self.manager._next_id = 1
        self.manager.speichere_daten()

    def save(self):
        return self.manager.speichere_daten()

    # Backwards compatibility helpers (GUI erwartete Namen)
    def speichere_daten(self):
        return self.save()