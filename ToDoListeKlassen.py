from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, date, timedelta
import calendar


class Aufgabe(ABC):
    """
    Abstrakte Basisklasse für Aufgaben.
    Enthält die gemeinsamen trivialen Methoden.
    """
    
    @abstractmethod
    def __str__(self) -> str:
        """String-Repräsentation der Aufgabe"""
        pass
    
    @abstractmethod
    def __repr__(self) -> str:
        """Developer-freundliche Repräsentation"""
        pass
    
    @abstractmethod
    def get_id(self) -> int:
        """Gibt die ID der Aufgabe zurück"""
        pass
    
    @abstractmethod
    def get_titel(self) -> str:
        """Gibt den Titel der Aufgabe zurück"""
        pass
    
    @abstractmethod
    def get_beschreibung(self) -> str:
        """Gibt die Beschreibung der Aufgabe zurück"""
        pass


class EinfacheAufgabe(Aufgabe):
    """
    Konkrete Klasse für einfache Aufgaben.
    Enthält die ersten Attribute: ID, Titel, Beschreibung, Status
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
        return f"Aufgabe #{self._id}: {self._titel} | Status: {self._status} | Beschreibung: {self._beschreibung}"
    
    def __repr__(self) -> str:
        return (f"EinfacheAufgabe(id={self._id}, titel='{self._titel}', "
                f"beschreibung='{self._beschreibung}', status='{self._status}')")
    
    def get_id(self) -> int:
        return self._id
    
    def get_titel(self) -> str:
        return self._titel
    
    def get_beschreibung(self) -> str:
        return self._beschreibung
    
    def get_status(self) -> str:
        return self._status
    
    def set_status(self, status: str) -> None:
        self._status = status

    



class TerminierteAufgabe(EinfacheAufgabe):
    """
    Erweiterte Aufgabe mit zusätzlichen Attributen:
    Fälligkeitsdatum, Verbleibend (Zeit), Wiederholung
    """
    
    def __init__(self,
                 id: int,
                 titel: str,
                 beschreibung: str,
                 status: str = "offen",
                 prio: int = 1,
                 faelligkeitsdatum: Optional[datetime] = None,
                 verbleibend: Optional[str] = None,
                 wiederholung: bool = False,
                 wiederholung_intervall: Optional[int]=None):
        super().__init__(id, titel, beschreibung, status)
        self.prio = prio
        self._faelligkeitsdatum = faelligkeitsdatum
        self._verbleibend = verbleibend
        self._wiederholung = wiederholung
        self._wiederholung_intervall = wiederholung_intervall
    
    def __str__(self) -> str:
        base = super().__str__()
        termin_info = f", Fällig: {self._faelligkeitsdatum.strftime('%d.%m.%Y') if self._faelligkeitsdatum else 'Nicht festgelegt'}"
        if self._verbleibend:
            termin_info += f", Verbleibend: {self._verbleibend}"
        if self._wiederholung:
            termin_info += ", Wiederholend"
        return base + termin_info
    
    def __repr__(self) -> str:
        return (f"TerminierteAufgabe(id={self._id}, titel='{self._titel}', "
                f"beschreibung='{self._beschreibung}', status='{self._status}', "
                f"prio={self.prio}, faelligkeitsdatum={self._faelligkeitsdatum}, "
                f"verbleibend='{self._verbleibend}', wiederholung={self._wiederholung})")
    
    def get_faelligkeitsdatum(self) -> Optional[datetime]:
        return self._faelligkeitsdatum
    
    def set_faelligkeitsdatum(self, datum: datetime) -> None:
        self._faelligkeitsdatum = datum
    
    def get_verbleibend(self) -> Optional[str]:
        return self._verbleibend

    def get_prio(self) -> int:
        return self.prio
    
    def get_wiederholung_intervall(self) -> Optional[int]:
        return self._wiederholung_intervall


    def set_prio(self, prio: int) -> None:
        self.prio = prio
    
    def set_verbleibend(self, verbleibend: str) -> None:
        self._verbleibend = verbleibend
    
    def ist_wiederholend(self) -> bool:
        return self._wiederholung
    
    def set_wiederholung(self) -> None:
        print("Wiederholungsintervall auswählen: ")
        print("1. Täglich\n2. Wöchentlich\n3. Monatlich\n4. Jährlich\n")
        while True:
            try:
                auswahl = int(input("> "))
                if auswahl in (1, 2, 3, 4):
                    break
                else:   
                    print("Bitte Zahl zwischen 1 und 4 eingeben.")
            except ValueError:
                print("Ungültige Eingabe, bitte Zahl eingeben.")

        self._wiederholung = True                # Aufgabe ist wiederholend
        self._wiederholung_intervall = auswahl    # Intervall speichern (1–4)
    
    def berechne_verbleibende_zeit(self) -> Optional[str]:
        """
        Berechnet die verbleibende Zeit bis zum Fälligkeitsdatum
        """
        if not self._faelligkeitsdatum:
            return None
        
        jetzt = datetime.now()
        differenz = self._faelligkeitsdatum - jetzt
        
        if differenz.days < 0:
            return f"Überfällig um {abs(differenz.days)} Tage"
        elif differenz.days == 0:
            return "Heute fällig"
        elif differenz.days == 1:
            return "1 Tag verbleibend"
        else:
            return f"{differenz.days} Tage verbleibend"

    def falligkeit_wiederholen(self) -> None:
        if not getattr(self, "_wiederholung", False):
            return
        if self._faelligkeitsdatum is None:
            return

        heute = datetime.now().date()
        
        # Konvertiere faellig zu date, falls es ein datetime ist
        if isinstance(self._faelligkeitsdatum, datetime):
            faellig = self._faelligkeitsdatum.date()
        else:
            faellig = self._faelligkeitsdatum
        
        while faellig <= heute:
            if self._wiederholung_intervall == 1:        # täglich
                faellig += timedelta(days=1)
            elif self._wiederholung_intervall == 2:      # wöchentlich
                faellig += timedelta(weeks=1)
            elif self._wiederholung_intervall == 3:      # monatlich
                month = faellig.month + 1
                year = faellig.year
                if month > 12:
                    month = 1
                    year += 1
                day = min(faellig.day, calendar.monthrange(year, month)[1])
                faellig = faellig.replace(year=year, month=month, day=day)
            elif self._wiederholung_intervall == 4:      # jährlich
                year = faellig.year + 1
                day = min(faellig.day, calendar.monthrange(year, faellig.month)[1])
                faellig = faellig.replace(year=year, day=day)
        
        self._faelligkeitsdatum =  datetime(faellig.year, faellig.month, faellig.day)
    
    def set_status(self, status):
        self._status = status
        heute = datetime.now().date()
        if isinstance(self._faelligkeitsdatum, datetime):
            faellig = self._faelligkeitsdatum.date()
        if faellig <= heute: 
            status = "überfällig"
            return status
        return self._status