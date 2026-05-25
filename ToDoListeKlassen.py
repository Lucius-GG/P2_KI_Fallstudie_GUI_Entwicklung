from datetime import datetime
from typing import Optional, Dict, Any

class Task:
    """Einfache Task‑Datenklasse mit kompatiblen Getter/Setter‑Methoden."""
    def __init__(self, id: str, titel: str, beschreibung: str = "", prio: int = 3, faellig: Optional[datetime] = None, status: str = "offen"):
        self.id = str(id)
        self.titel = titel
        self.beschreibung = beschreibung
        self.prio = int(prio) if prio is not None else 3
        self.faellig = faellig  # datetime or None
        self.status = status

    # Getter (kompatibel mit GUI)
    def get_id(self) -> str: return self.id
    def get_titel(self) -> str: return self.titel
    def get_beschreibung(self) -> str: return self.beschreibung
    def get_prio(self) -> int: return self.prio
    def get_faelligkeitsdatum(self) -> Optional[datetime]: return self.faellig
    def get_status(self) -> str: return self.status

    # Setter / Mutatoren
    def set_status(self, status: str): self.status = status
    def set_titel(self, titel: str): self.titel = titel
    def set_beschreibung(self, beschreibung: str): self.beschreibung = beschreibung
    def set_prio(self, prio: int): self.prio = int(prio)
    def set_faelligkeitsdatum(self, faellig: Optional[datetime]): self.faellig = faellig

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "titel": self.titel,
            "beschreibung": self.beschreibung,
            "prio": self.prio,
            "faellig": self.faellig.isoformat() if self.faellig else None,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Task":
        faellig = None
        if d.get("faellig"):
            try:
                faellig = datetime.fromisoformat(d["faellig"])
            except Exception:
                faellig = None
        return Task(
            id=str(d.get("id")),
            titel=d.get("titel", ""),
            beschreibung=d.get("beschreibung", ""),
            prio=int(d.get("prio", 3)),
            faellig=faellig,
            status=d.get("status", "offen"),
        )

    def __repr__(self):
        return f"<Task {self.id} '{self.titel}' status={self.status}>"