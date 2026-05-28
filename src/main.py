"""Einstiegspunkt fuer DevPulse Planner.

Startet die grafische Tkinter-Oberflaeche.
"""

from GUI import DevPulsePlanner


def main():
    """Startet die GUI-Anwendung."""
    app = DevPulsePlanner()
    app.mainloop()


if __name__ == "__main__":
    main()