from Manager import AufgabenManager

from ToDoListeKlassen import EinfacheAufgabe, TerminierteAufgabe
from tabulate import tabulate
from datetime import datetime, timedelta

def get_valid_id(manager: AufgabenManager):
    while True:
        try:
            id = int(input("Gib eine ID an: "))
            if id in manager.aufgaben:
                print(f"Fehler: ID {id} ist bereits vergeben. Bitte wähle eine andere ID.")
            else:
                return id
        except ValueError:
            print("Bitte gib eine gültige Zahl ein.")

def id_eingabe(manager: AufgabenManager):
    while True:
        try:
            id = int(input("Gib eine ID an: "))
            return id
        except ValueError:
            print("Bitte gib eine gültige Zahl ein.")


def get_valid_priority():
    prio_map = {"niedrig": 1, "mittel": 3, "hoch": 5}
    while True:
        prio_input = input("Priorität (niedrig/mittel/hoch): ").strip().lower()
        if prio_input in prio_map:
            return prio_map[prio_input]
        else:
            print("Ungültige Eingabe. Bitte 'niedrig', 'mittel' oder 'hoch' eingeben.")

def get_yes_no(frage: str):
    while True:
        antwort = input(f"{frage} (ja/nein): ").strip().lower()
        if antwort in ["ja", "j", "yes", "y"]:
            return True
        elif antwort in ["nein", "n", "no"]:
            return False
        else:
            print("Ungültige Eingabe. Bitte 'ja' oder 'nein' eingeben.")

def get_valid_date():
    print("\nFälligkeitsdatum eingeben:")
    print("1. Heute")
    print("2. Morgen")
    print("3. In einer Woche")
    print("4. Eigenes Datum (YYYY-MM-DD)")
    while True:
        auswahl = input("Auswahl: ").strip()
        if auswahl == "1":
            return datetime.now()
        elif auswahl == "2":
            return datetime.now() + timedelta(days=1)
        elif auswahl == "3":
            return datetime.now() + timedelta(weeks=1)
        elif auswahl == "4":
            while True:
                datum = input("Datum (YYYY-MM-DD): ")
                try:
                    return datetime.strptime(datum, "%Y-%m-%d")
                except ValueError:
                    print("Bitte gib ein gültiges Datum im Format YYYY-MM-DD ein.")
        else:
            print("Ungültige Eingabe. Bitte 1-4 wählen.")

def lade_demo(manager: AufgabenManager):
    # Demo-Aufgaben hinzufügen
    manager.aufgabe_hinzufuegen(TerminierteAufgabe(1, "Staubsaugen", "Wohnzimmer staubsaugen", "erledigt", 1, datetime.now()+timedelta(days=2), None, False))
    manager.aufgabe_hinzufuegen(TerminierteAufgabe(2, "Mathe lernen", "Aufgabenblatt 3", "offen", 3, datetime(2025,12,1), None, False))
    manager.aufgabe_hinzufuegen(TerminierteAufgabe(3, "Einkaufen", "Milch+Brot kaufen", "offen", 5, datetime.now()+timedelta(days=5), None, True))
    manager.aufgabe_hinzufuegen(TerminierteAufgabe(4, "Test", "Test", 'erledigt', 1, datetime(2025,11,23), None, True))
    print("Demo-Aufgaben wurden geladen.")

def interface():
    manager = AufgabenManager()
    print("Programm gestartet. Wähle '11' zum Laden der Demo, '10' zum Beenden.")

    while True:
        print("\n--- ToDo-Liste Interface ---")
        print("1. Neue Aufgabe hinzufügen")
        print("2. Aufgabe entfernen")
        print("3. Aufgabe wiederherstellen")
        print("4. Aufgabe als erledigt markieren")
        print("5. Priorität setzen")
        print("6. Fälligkeitsdatum setzen")
        print("7. Alle Aufgaben anzeigen")
        print("8. Nach Priorität filtern")
        print("9. Suche")
        print("10. Beenden")
        print("11. Demo laden")

        auswahl = input("Deine Auswahl: ").strip()

        if auswahl == "10":
            print("Programm beendet.")
            break

        elif auswahl == "11":
            lade_demo(manager)

        elif auswahl == "1":
            aufgabe_id = get_valid_id(manager)
            titel = input("Titel: ")
            beschreibung = input("Beschreibung: ")
            erweitert = get_yes_no("Erweiterte Aufgabe? (Termin, Wiederholung, Prio)")
            if erweitert:
                faellig = get_valid_date()
                prio = get_valid_priority()

                aufgabe = TerminierteAufgabe(aufgabe_id, titel, beschreibung, "offen", prio)
                aufgabe.set_faelligkeitsdatum(faellig)

                if get_yes_no("Wiederholende Aufgabe? "):
                 aufgabe.set_wiederholung()
                 aufgabe.falligkeit_wiederholen()
            else:
                aufgabe = EinfacheAufgabe(aufgabe_id, titel, beschreibung)
            manager.aufgabe_hinzufuegen(aufgabe)
            print("Aufgabe hinzugefügt.")

        elif auswahl == "2":
            aufgabe_id = id_eingabe(manager)
            manager.aufgabe_entfernen(aufgabe_id)
            print("Aufgabe entfernt.")

        elif auswahl == "3":
            aid = id_eingabe(manager)
            manager.aufgabe_wiederherstellen(aid)
            print("Aufgabe wiederhergestellt.")

        elif auswahl == "4":
            aid = id_eingabe(manager)
            manager.erledigt_setzen(aid)
            print("Aufgabe als erledigt markiert.")

        elif auswahl == "5":
            aid = id_eingabe(manager)
            if aid not in manager.aufgaben:
                print(f"Aufgabe mit ID {aid} existiert nicht.")
            else:
                # Prüfe, ob die Aufgabe einen Prioritäts-Slot hat
                aufgabe = manager.aufgaben[aid]
                if hasattr(aufgabe, "set_prio"):
                    prio = get_valid_priority()
                    manager.prioritaet_setzen(aid, prio)
                    print(f"Priorität für Aufgabe {aid} gesetzt.")
                else:
                    print("Diese Aufgabe unterstützt keine Priorität.")

        elif auswahl == "6":
            aid = id_eingabe(manager)
            datum = get_valid_date()
            manager.faelligkeit_setzen(aid, datum)
            print("Fälligkeitsdatum gesetzt.")

        elif auswahl == "7":
            print("\nAlle Aufgaben:")
            prio_map = {1: "Niedrig", 3: "Mittel", 5: "Hoch"}
            data = []

            
            for a in manager.aufgaben.values():
                prio_val = a.get_prio() if hasattr(a, "get_prio") else None
                prio_text = prio_map.get(prio_val, "-") if prio_val else "-"
                intervall_map = {1: "Täglich", 2: "Wöchentlich", 3: "Monatlich", 4: "Jährlich"}
                intervall_val = a.get_wiederholung_intervall() if hasattr(a, "get_wiederholung_intervall") else None
                intervall_text = intervall_map.get(intervall_val, "-") if intervall_val else "-"
                row = [
                    a.get_id(),
                    a.get_titel(),
                    a.get_beschreibung(),
                    a.set_status(a.get_status()),
                    prio_text,
                    a.get_faelligkeitsdatum().strftime("%d.%m.%Y") if hasattr(a, "get_faelligkeitsdatum") and a.get_faelligkeitsdatum() else "-",
                    "Ja" if hasattr(a, "ist_wiederholend") and a.ist_wiederholend() else "Nein",
                    intervall_text  # ← Hier verwenden
                ]
                data.append(row)
            if data:
                print(tabulate(data, headers=["ID", "Titel", "Beschreibung", "Status", "Priorität", "Fällig", "Wiederholend", "Wiederholung Intervall"], tablefmt="grid"))
            else:
                print("Keine Aufgaben vorhanden.")

        elif auswahl == "8":
            prio = get_valid_priority()
            prio_map = {1: "Niedrig", 3: "Mittel", 5: "Hoch"}
            print(f"\nAufgaben mit Priorität {prio_map[prio]}:")
            data = []
            for a in manager.aufgaben.values():
                prio_val = a.get_prio() if hasattr(a, "get_prio") else None
                if prio_val == prio:
                    row = [
                        a.get_id(),
                        a.get_titel(),
                        a.get_beschreibung(),
                        a.get_status(),
                        a.get_faelligkeitsdatum().strftime("%d.%m.%Y") if hasattr(a, "get_faelligkeitsdatum") and a.get_faelligkeitsdatum() else "-",
                        "Ja" if hasattr(a, "ist_wiederholend") and a.ist_wiederholend() else "Nein"
                    ]
                    data.append(row)
            if data:
                print(tabulate(data, headers=["ID", "Titel", "Beschreibung", "Status", "Fällig", "Wiederholend"], tablefmt="grid"))
            else:
                print("Keine Aufgaben mit dieser Priorität gefunden.")

        elif auswahl == "9":
            wort = input("Suchwort: ")
            print(f"\nSuchergebnisse für '{wort}':")
            prio_map = {1: "Niedrig", 3: "Mittel", 5: "Hoch"}
            data = []
            for a in manager.aufgaben.values():
                if wort.lower() in a.get_titel().lower() or wort.lower() in a.get_beschreibung().lower():
                    prio_val = a.get_prio() if hasattr(a, "get_prio") else None
                    prio_text = prio_map.get(prio_val, "-") if prio_val else "-"
                    row = [
                        a.get_id(),
                        a.get_titel(),
                        a.get_beschreibung(),
                        a.get_status(),
                        prio_text,
                        a.get_faelligkeitsdatum().strftime("%d.%m.%Y") if hasattr(a, "get_faelligkeitsdatum") and a.get_faelligkeitsdatum() else "-",
                        "Ja" if hasattr(a, "ist_wiederholend") and a.ist_wiederholend() else "Nein"
                    ]
                    data.append(row)
            if data:
                print(tabulate(data, headers=["ID", "Titel", "Beschreibung", "Status", "Priorität", "Fällig", "Wiederholend"], tablefmt="grid"))
            else:
                print("Keine Suchergebnisse gefunden.")

        else:
            print("Ungültige Eingabe.")

if __name__ == "__main__":
    interface()
