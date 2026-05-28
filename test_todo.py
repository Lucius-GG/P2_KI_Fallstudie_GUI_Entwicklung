import pytest
import os
import tempfile
from datetime import datetime, timedelta
from Manager import TaskManager
from ToDoListeKlassen import Task


# ---------------------------------------------------------
#   FIXTURES
# ---------------------------------------------------------

@pytest.fixture
def temp_storage():
    """Erstellt eine temporäre Datei für jeden Test"""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    # Cleanup nach Test
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def manager(temp_storage):
    """Erstellt einen TaskManager mit temporärem Speicher"""
    return TaskManager(storage_path=temp_storage)


# ---------------------------------------------------------
#   TESTS FÜR Task (Einfache Aufgabe)
# ---------------------------------------------------------

def test_task_basic():
    """Test: Basis-Task erstellen und Getter/Setter"""
    t = Task("1", "Test", "Beschreibung")

    assert t.get_id() == "1"
    assert t.get_titel() == "Test"
    assert t.get_beschreibung() == "Beschreibung"
    assert t.get_status() == "offen"

    t.set_status("erledigt")
    assert t.get_status() == "erledigt"


def test_task_mit_prio_und_faelligkeit():
    """Test: Task mit Priorität und Fälligkeitsdatum"""
    faellig = datetime.now() + timedelta(days=3)
    t = Task("2", "Termin", "Test", prio=3, faellig=faellig)

    assert t.get_prio() == 3
    assert t.get_faelligkeitsdatum() is not None


def test_verbleibende_zeit_berechnung():
    """Test: Fälligkeitsdatum ist korrekt gespeichert"""
    morgen = datetime.now() + timedelta(days=1)
    t = Task("3", "Zeit", "Test", faellig=morgen)

    result = t.get_faelligkeitsdatum()
    assert isinstance(result, datetime)


def test_status_setzen():
    """Test: Status ändern funktioniert"""
    t = Task("5", "Überfällig", "Test", faellig=datetime.now() - timedelta(days=1))

    t.set_status("in_bearbeitung")
    assert t.get_status() == "in_bearbeitung"


def test_task_default_values():
    """Test: Default-Werte werden korrekt gesetzt"""
    t = Task("10", "MinimalTask")
    
    assert t.get_prio() == 3  # Default
    assert t.get_beschreibung() == ""
    assert t.get_faelligkeitsdatum() is None
    assert t.get_status() == "offen"


# ---------------------------------------------------------
#   TESTS FÜR TaskManager
# ---------------------------------------------------------

def test_task_hinzufuegen(manager):
    """Test: Task hinzufügen"""
    task_id = manager.add_task("Test", "Beschreibung")

    assert task_id in manager.aufgaben
    assert manager.aufgaben[task_id].get_titel() == "Test"


def test_task_entfernen(manager):
    """Test: Task entfernen und Tracking"""
    task_id = manager.add_task("Test", "Beschreibung")
    
    assert task_id in manager.aufgaben
    success = manager.aufgabe_entfernen(task_id)
    
    assert success is True
    assert task_id not in manager.aufgaben
    assert len(manager.geloescht) > 0


def test_task_entfernen_nicht_existent(manager):
    """Test: Nicht-existente Task entfernen fehlgeschlagen"""
    success = manager.aufgabe_entfernen("nicht_vorhanden")
    
    assert success is False


def test_task_komplett(manager):
    """Test: Task als erledigt markieren"""
    task_id = manager.add_task("Test", "Beschreibung")

    manager.complete_task(task_id)
    assert manager.aufgaben[task_id].get_status() == "erledigt"


def test_task_in_bearbeitung(manager):
    """Test: Task in Bearbeitung setzen"""
    task_id = manager.add_task("Test", "Beschreibung")

    manager.bearbeitung_task(task_id)
    assert manager.aufgaben[task_id].get_status() == "in_bearbeitung"


def test_prioritaet_setzen(manager):
    """Test: Priorität ändern"""
    task_id = manager.add_task("Test", "Beschreibung", prio=1)
    task = manager.get_task(task_id)

    task.set_prio(5)
    assert task.get_prio() == 5


def test_faelligkeit_setzen(manager):
    """Test: Fälligkeitsdatum ändern"""
    task_id = manager.add_task("Test", "Beschreibung")
    datum = datetime.now() + timedelta(days=10)

    task = manager.get_task(task_id)
    task.set_faelligkeitsdatum(datum)

    assert manager.aufgaben[task_id].get_faelligkeitsdatum() is not None


def test_get_tasks_by_status(manager):
    """Test: Tasks nach Status filtern"""
    manager.add_task("A", "B", status="offen")
    manager.add_task("C", "D", status="erledigt")

    result = manager.get_tasks_by_status("erledigt")
    assert len(result) == 1
    assert result[0].get_titel() == "C"


def test_get_tasks_by_status_mehrere(manager):
    """Test: Mehrere Tasks mit gleichem Status"""
    manager.add_task("A", "B", status="offen")
    manager.add_task("C", "D", status="offen")
    manager.add_task("E", "F", status="erledigt")

    result = manager.get_tasks_by_status("offen")
    assert len(result) == 2


def test_task_to_dict_from_dict():
    """Test: Serialisierung und Deserialisierung"""
    t = Task("1", "Test", "Beschreibung", prio=2, status="in_bearbeitung")
    d = t.to_dict()

    t2 = Task.from_dict(d)
    assert t2.get_id() == "1"
    assert t2.get_titel() == "Test"
    assert t2.get_prio() == 2
    assert t2.get_status() == "in_bearbeitung"


def test_task_persistence(temp_storage):
    """Test: Datenspeicherung und Laden"""
    manager1 = TaskManager(storage_path=temp_storage)
    task_id = manager1.add_task("Persistent", "Sollte geladen werden")
    
    # Neuer Manager mit gleicher Datei
    manager2 = TaskManager(storage_path=temp_storage)
    
    assert task_id in manager2.aufgaben
    assert manager2.aufgaben[task_id].get_titel() == "Persistent"


def test_get_nonexistent_task(manager):
    """Test: Nicht-existente Task abrufen"""
    task = manager.get_task("nicht_vorhanden")
    assert task is None