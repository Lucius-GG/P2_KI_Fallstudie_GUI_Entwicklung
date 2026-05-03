from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timedelta


class Aufgabe(ABC):
    """
    Abstrakte Basisklasse für Aufgaben.
    Enthält die gemeinsamen Methoden.
    """
    
    @abstractmethod
    def get_id(self) -> int:
        pass
    
    @abstractmethod
    def get_titel(self) -> str:
        pass
    
    @abstractmethod
    def get_beschreibung(self) -> str:
        pass
    
    @abstractmethod
    def get_status(self) -> str:
        pass
    
    @abstractmethod
    def set_status(self, status: str) -> None:
        pass


class EinfacheAufgabe(Aufgabe):
    """
    Konkrete Klasse für einfache Aufgaben.
    Attribute: ID, Titel, Beschreibung, Status
    """
    
    def __init__(self,
                 id: int,
                 titel: str,
                 beschreibung: str, 
                 status: str = "offen"):
        self._id = id
        self._titel = titel
        self._beschreibung = beschreibung
        self._status = status
    
    def __str__(self) -> str:
        return f"[{self._id}] {self._titel} - Status: {self._status}"
    
    def __repr__(self) -> str:
        return f"EinfacheAufgabe({self._id}, '{self._titel}', '{self._status}')"
    
    def get_id(self) -> int:
        return self._id
    
    def get_titel(self) -> str:
        return self._titel
    
    def get_beschreibung(self) -> str:
        return self._beschreibung
    
    def get_status(self) -> str:
        return self._status
    
    def set_status(self, status: str) -> None:
        if status in ["offen", "erledigt", "in_bearbeitung"]:
            self._status = status
        else:
            raise ValueError(f"Ungültiger Status: {status}")


class TerminierteAufgabe(EinfacheAufgabe):
    """
    Erweiterte Aufgabe mit zusätzlichen Attributen:
    Priorität, Fälligkeitsdatum, Wiederholung
    """
    
    def __init__(self,
                 id: int,
                 titel: str,
                 beschreibung: str,
                 status: str = "offen",
                 prio: int = 1,
                 faelligkeitsdatum: Optional[datetime] = None,
                 wiederholung: bool = False,
                 wiederholung_intervall: Optional[int] = None):
        super().__init__(id, titel, beschreibung, status)
        self._prio = prio
        self._faelligkeitsdatum = faelligkeitsdatum
        self._wiederholung = wiederholung
        self._wiederholung_intervall = wiederholung_intervall
    
    def __str__(self) -> str:
        datum_str = self._faelligkeitsdatum.strftime("%d.%m.%Y") if self._faelligkeitsdatum else "Kein Datum"
        return f"[{self._id}] {self._titel} - Prio: {self._prio} - Fällig: {datum_str} - Status: {self._status}"
    
    def __repr__(self) -> str:
        return f"TerminierteAufgabe({self._id}, '{self._titel}', Prio={self._prio})"
    
    def get_prio(self) -> int:
        return self._prio
    
    def set_prio(self, prio: int) -> None:
        if prio in [1, 3, 5]:
            self._prio = prio
        else:
            raise ValueError("Priorität muss 1, 3 oder 5 sein")
    
    def get_faelligkeitsdatum(self) -> Optional[datetime]:
        return self._faelligkeitsdatum
    
    def set_faelligkeitsdatum(self, datum: datetime) -> None:
        self._faelligkeitsdatum = datum
    
    def get_wiederholung(self) -> bool:
        return self._wiederholung
    
    def set_wiederholung(self, wiederholung: bool = True) -> None:
        self._wiederholung = wiederholung
    
    def get_wiederholung_intervall(self) -> Optional[int]:
        return self._wiederholung_intervall
    
    def set_wiederholung_intervall(self, intervall: int) -> None:
        self._wiederholung_intervall = intervall
    
    def falligkeit_wiederholen(self) -> None:
        """Berechnet nächstes Fälligkeitsdatum basierend auf Intervall"""
        if self._wiederholung and self._wiederholung_intervall and self._faelligkeitsdatum:
            self._faelligkeitsdatum = self._faelligkeitsdatum + timedelta(days=self._wiederholung_intervall)