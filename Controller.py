from Manager import AufgabenManager
from ToDoListeKlassen import EinfacheAufgabe, TerminierteAufgabe
from datetime import datetime, timedelta


class PlannerController:
    """
    Controller zwischen GUI und Business-Logic.
    Verarbeitet alle Benutzeraktionen und aktualisiert Model + View.
    """
    
    def __init__(self, view=None):
        self.manager = AufgabenManager()
        self.view = view
        
    # ===== AUFGABEN ERSTELLEN =====
    def add_task(self, titel: str, beschreibung: str, prio: int = 1, 
                 faellig: datetime = None, wiederholend: bool = False) -> int:
        """Fügt eine neue Aufgabe hinzu und gibt die ID zurück"""
        aufgabe_id = max(self.manager.aufgaben.keys(), default=0) + 1
        
        if faellig or wiederholend:
            aufgabe = TerminierteAufgabe(
                aufgabe_id, titel, beschreibung, "offen", prio, faellig
            )
            if wiederholend:
                aufgabe.set_wiederholung()
        else:
            aufgabe = EinfacheAufgabe(aufgabe_id, titel, beschreibung, "offen")
        
        self.manager.aufgabe_hinzufuegen(aufgabe)
        
        if self.view:
            self.view.refresh_board()
        
        return aufgabe_id
    
    # ===== AUFGABEN VERWALTEN =====
    def get_all_tasks(self) -> dict:
        """Gibt alle Aufgaben zurück"""
        return self.manager.aufgaben
    
    def get_tasks_by_status(self, status: str) -> list:
        """Filtert Aufgaben nach Status"""
        return self.manager.nach_status_filtern(status)
    
    def get_tasks_by_priority(self, prio: int) -> list:
        """Filtert Aufgaben nach Priorität"""
        return self.manager.nach_prioritaet_filtern(prio)
    
    def complete_task(self, task_id: int):
        """Markiert eine Aufgabe als erledigt"""
        self.manager.erledigt_setzen(task_id)
        if self.view:
            self.view.refresh_board()
    
    def delete_task(self, task_id: int):
        """Löscht eine Aufgabe"""
        self.manager.aufgabe_entfernen(task_id)
        if self.view:
            self.view.refresh_board()
    
    def restore_task(self, task_id: int):
        """Stellt eine gelöschte Aufgabe wieder her"""
        self.manager.aufgabe_wiederherstellen(task_id)
        if self.view:
            self.view.refresh_board()
    
    def set_priority(self, task_id: int, prio: int):
        """Setzt die Priorität einer Aufgabe"""
        self.manager.prioritaet_setzen(task_id, prio)
        if self.view:
            self.view.refresh_board()
    
    def set_deadline(self, task_id: int, datum: datetime):
        """Setzt das Fälligkeitsdatum"""
        self.manager.faelligkeit_setzen(task_id, datum)
        if self.view:
            self.view.refresh_board()
    
    # ===== FILTERUNG & SUCHE =====
    def search_tasks(self, keyword: str) -> list:
        """Sucht nach Aufgaben"""
        return self.manager.suche(keyword)
    
    def filter_by_priority(self, prio: int) -> list:
        """Filtert nach Priorität"""
        return self.manager.nach_prioritaet_filtern(prio)
    
    # ===== DEMO-DATEN =====
    def load_demo_data(self):
        """Lädt Demo-Aufgaben"""
        self.manager.aufgabe_hinzufuegen(TerminierteAufgabe(
            1, "GUI Refinement", "Logo auf Vektor-Basis umgestellt", 
            "in_bearbeitung", 5, datetime.now()
        ))
        self.manager.aufgabe_hinzufuegen(TerminierteAufgabe(
            2, "KI Fallstudie", "Integration der ToDoListeKlassen", 
            "offen", 3, datetime(2026, 5, 29)
        ))
        self.manager.aufgabe_hinzufuegen(TerminierteAufgabe(
            3, "DPI Bugfix", "High-DPI Awareness für Windows 11", 
            "erledigt", 1, datetime.now() - timedelta(days=2)
        ))
        self.manager.aufgabe_hinzufuegen(TerminierteAufgabe(
            4, "Testing", "Unit Tests für Manager schreiben", 
            "offen", 3, datetime(2026, 6, 1)
        ))
        if self.view:
            self.view.refresh_board()