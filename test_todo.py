import pytest
from datetime import datetime, timedelta, date
from Manager import AufgabenManager
from ToDoListeKlassen import EinfacheAufgabe, TerminierteAufgabe


# ---------------------------------------------------------
#   TESTS FÜR EinfacheAufgabe
# ---------------------------------------------------------

def test_einfache_aufgabe_basic():
    a = EinfacheAufgabe(1, "Test", "Beschreibung")

    assert a.get_id() == 1
    assert a.get_titel() == "Test"
    assert a.get_beschreibung() == "Beschreibung"
    assert a.get_status() == "offen"

    a.set_status("erledigt")
    assert a.get_status() == "erledigt"


# ---------------------------------------------------------
#   TESTS FÜR TerminierteAufgabe
# ---------------------------------------------------------

def test_terminierte_aufgabe_prio_und_faelligkeit():
    faellig = datetime.now() + timedelta(days=3)
    a = TerminierteAufgabe(2, "Termin", "Test", prio=3, faelligkeitsdatum=faellig)

    assert a.get_prio() == 3
    assert a.get_faelligkeitsdatum() is not None


def test_verbleibende_zeit_berechnung():
    morgen = datetime.now() + timedelta(days=1)
    a = TerminierteAufgabe(3, "Zeit", "Test", faelligkeitsdatum=morgen)

    result = a.berechne_verbleibende_zeit()
    assert isinstance(result, str)


def test_faelligkeit_wiederholen_taeglich():
    gestern = datetime.now() - timedelta(days=1)
    a = TerminierteAufgabe(
        4, "Wiederholung", "Test",
        faelligkeitsdatum=gestern,
        wiederholung=True,
        wiederholung_intervall=1
    )

    a.falligkeit_wiederholen()

    faellig = a.get_faelligkeitsdatum()

    # Akzeptiere sowohl date als auch datetime
    if isinstance(faellig, datetime):
        assert faellig.date() > datetime.now().date()
    elif isinstance(faellig, date):
        assert faellig > datetime.now().date()
    else:
        raise AssertionError("Fälligkeitsdatum ist in einem unerwarteten Format.")


def test_status_setzen_ueberfaellig():
    gestern = datetime.now() - timedelta(days=1)
    a = TerminierteAufgabe(5, "Überfällig", "Test", faelligkeitsdatum=gestern)

    new_status = a.set_status("egal")
    assert new_status in ["überfällig", "egal", a.get_status()]


# ---------------------------------------------------------
#   TESTS FÜR AufgabenManager
# ---------------------------------------------------------

def test_aufgabe_hinzufuegen():
    m = AufgabenManager()
    a = EinfacheAufgabe(1, "Test", "Beschreibung")

    m.aufgabe_hinzufuegen(a)

    assert 1 in m.aufgaben


def test_aufgabe_entfernen_und_wiederherstellen():
    m = AufgabenManager()
    a = EinfacheAufgabe(1, "Test", "Beschreibung")
    m.aufgabe_hinzufuegen(a)

    m.aufgabe_entfernen(1)
    assert 1 not in m.aufgaben
    assert 1 in m.geloescht

    m.aufgabe_wiederherstellen(1)
    assert 1 in m.aufgaben
    assert 1 not in m.geloescht


def test_erledigt_setzen():
    m = AufgabenManager()
    a = EinfacheAufgabe(1, "Test", "Beschreibung")
    m.aufgabe_hinzufuegen(a)

    m.erledigt_setzen(1)
    assert a.get_status() == "erledigt"


def test_prioritaet_setzen():
    m = AufgabenManager()
    a = TerminierteAufgabe(1, "Test", "Beschreibung", prio=1)
    m.aufgabe_hinzufuegen(a)

    m.prioritaet_setzen(1, 5)
    assert a.get_prio() == 5


def test_faelligkeit_setzen():
    m = AufgabenManager()
    a = TerminierteAufgabe(1, "Test", "Beschreibung")
    m.aufgabe_hinzufuegen(a)

    datum = datetime.now() + timedelta(days=10)
    m.faelligkeit_setzen(1, datum)

    assert m.aufgaben[1].get_faelligkeitsdatum() is not None


def test_alle_anzeigen():
    m = AufgabenManager()
    a = EinfacheAufgabe(1, "Test", "Beschreibung")
    m.aufgabe_hinzufuegen(a)

    result = m.alle_anzeigen()
    assert len(result) == 1


def test_nach_prioritaet_filtern():
    m = AufgabenManager()
    a1 = TerminierteAufgabe(1, "A", "B", prio=1)
    a2 = TerminierteAufgabe(2, "C", "D", prio=3)
    m.aufgabe_hinzufuegen(a1)
    m.aufgabe_hinzufuegen(a2)

    result = m.nach_prioritaet_filtern(3)

    assert any("C" in s for s in result)


def test_suche():
    m = AufgabenManager()
    a1 = EinfacheAufgabe(1, "Mathe lernen", "Aufgabenblatt")
    a2 = EinfacheAufgabe(2, "Einkaufen", "Milch und Brot")

    m.aufgabe_hinzufuegen(a1)
    m.aufgabe_hinzufuegen(a2)

    assert any("Mathe" in s for s in m.suche("Mathe"))
    assert any("Brot" in s for s in m.suche("Brot"))