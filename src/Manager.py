import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ToDoListeKlassen import Task

_STORAGE_FILENAME = "tasks.json"

class TaskManager:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(os.path.dirname(__file__), _STORAGE_FILENAME)
        self.aufgaben: Dict[str, Task] = {}
        self.geloescht: List[str] = []
        self._next_id = 1
        self.load()

    def _gen_id(self) -> str:
        nid = str(self._next_id)
        self._next_id += 1
        return nid

    def add_task(self, titel: str, beschreibung: str = "", prio: int = 3, faellig: Optional[datetime] = None, status: str = "offen") -> str:
        tid = self._gen_id()
        task = Task(tid, titel, beschreibung, prio, faellig, status)
        self.aufgaben[tid] = task
        self.speichere_daten()
        return tid

    def aufgabe_entfernen(self, task_id: str) -> bool:
        task = self.aufgaben.pop(str(task_id), None)
        if not task:
            return False

        # Einfach: wenn möglich to_dict nutzen, sonst __dict__ oder repr speichern
        if hasattr(task, "to_dict") and callable(task.to_dict):
            record = task.to_dict()
        else:
            record = getattr(task, "__dict__", {"id": str(task_id)})
            if not isinstance(record, dict):
                record = {"id": str(task_id), "repr": repr(task)}

        self.geloescht.append(record)
        self.speichere_daten()
        return True

    def get_task(self, task_id: str):
        return self.aufgaben.get(str(task_id))

    def get_tasks_by_status(self, status: str):
        return [t for t in self.aufgaben.values() if t.get_status() == status]

    def move_task(self, task_id: str, target_status: str) -> bool:
        t = self.get_task(task_id)
        if not t:
            return False
        t.set_status(target_status)
        self.speichere_daten()
        return True

    def complete_task(self, task_id: str) -> bool:
        return self.move_task(task_id, "erledigt")

    def bearbeitung_task(self, task_id: str) -> bool:
        return self.move_task(task_id, "in_bearbeitung")

    def speichere_daten(self):
        data = {"tasks": [t.to_dict() for t in self.aufgaben.values()], "geloescht": list(self.geloescht), "_next_id": self._next_id}
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tasks = data.get("tasks", [])
            for d in tasks:
                # Normalisiere mögliche Schlüsselvarianten aus daten.json
                if "faelligkeit" in d and "faellig" not in d:
                    d["faellig"] = d.pop("faelligkeit")
                # id kann numerisch sein -> string
                if "id" in d:
                    d["id"] = str(d["id"])
                t = Task.from_dict(d)
                self.aufgaben[t.get_id()] = t
            self.geloescht = data.get("geloescht", [])
            self._next_id = int(data.get("_next_id", max((int(k) for k in self.aufgaben.keys()), default=0) + 1))
        except Exception:
            self.aufgaben = {}
            self.geloescht = []
            self._next_id = 1