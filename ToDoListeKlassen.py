from datetime import datetime
from typing import Optional, Dict, Any


class Task:
    """
    Einfache Task-Datenklasse mit kompatiblen Getter/Setter-Methoden.
    Verwaltet eine einzelne Aufgabe mit allen relevanten Informationen.
    """

    # ===== KONSTRUKTOR =====
    # Initialisiert eine neue Task mit allen erforderlichen Eigenschaften
    def __init__(
        self,
        id: str,
        titel: str,
        beschreibung: str = "",
        prio: int = 3,
        faellig: Optional[datetime] = None,
        status: str = "offen"
    ):
        self.id = str(id)
        self.titel = titel
        self.beschreibung = beschreibung
        self.prio = int(prio) if prio is not None else 3
        self.faellig = faellig  # datetime or None
        self.status = status

    # ===== GETTER-METHODEN =====
    # Alle Getter-Methoden zum Abrufen der Task-Eigenschaften
    def get_id(self) -> str:
        """Gibt die eindeutige ID der Task zurück"""
        return self.id

    def get_titel(self) -> str:
        """Gibt den Titel der Task zurück"""
        return self.titel

    def get_beschreibung(self) -> str:
        """Gibt die Beschreibung der Task zurück"""
        return self.beschreibung

    def get_prio(self) -> int:
        """Gibt die Priorität der Task zurück (1-5)"""
        return self.prio

    def get_faelligkeitsdatum(self) -> Optional[datetime]:
        """Gibt das Fälligkeitsdatum der Task zurück (oder None)"""
        return self.faellig

    def get_status(self) -> str:
        """Gibt den aktuellen Status der Task zurück"""
        return self.status

    # ===== SETTER-METHODEN =====
    # Alle Setter-Methoden zum Ändern der Task-Eigenschaften
    def set_status(self, status: str) -> None:
        """Setzt den Status der Task"""
        self.status = status

    def set_titel(self, titel: str) -> None:
        """Ändert den Titel der Task"""
        self.titel = titel

    def set_beschreibung(self, beschreibung: str) -> None:
        """Ändert die Beschreibung der Task"""
        self.beschreibung = beschreibung

    def set_prio(self, prio: int) -> None:
        """Ändert die Priorität der Task"""
        self.prio = int(prio)

    def set_faelligkeitsdatum(self, faellig: Optional[datetime]) -> None:
        """Ändert das Fälligkeitsdatum der Task"""
        self.faellig = faellig

    # ===== SERIALISIERUNG =====
    # Konvertiert die Task in ein Dictionary für die Speicherung
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Task-Objekt in ein Dictionary.
        Das Fälligkeitsdatum wird als ISO-Format-String gespeichert.
        """
        return {
            "id": self.id,
            "titel": self.titel,
            "beschreibung": self.beschreibung,
            "prio": self.prio,
            "faellig": self.faellig.isoformat() if self.faellig else None,
            "status": self.status,
        }

    # ===== DESERIALISIERUNG =====
    # Erstellt eine Task aus einem Dictionary (z.B. aus JSON geladen)
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Task":
        """
        Erstellt eine Task-Objekt aus einem Dictionary.
        Konvertiert das ISO-Format-String zurück zu einem datetime-Objekt.
        """
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

    # ===== DARSTELLUNG =====
    # Definiert, wie die Task als Text ausgegeben wird
    def __repr__(self) -> str:
        """Gibt eine lesbare Repräsentation der Task zurück"""
        return f"<Task {self.id} '{self.titel}' status={self.status}>"