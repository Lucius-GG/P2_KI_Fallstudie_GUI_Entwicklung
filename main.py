from GUI import DevPulsePlanner


def main():
    """Startet die komplette Anwendung"""
    print("\n" + "="*70)
    print("🚀 DEVPULSE PLANNER - Task Management System")
    print("="*70)
    print("\n📌 Starte GUI-Anwendung...\n")
    
    app = DevPulsePlanner()
    app.mainloop()
    
    print("\n" + "="*70)
    print("✅ Auf Wiedersehen!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
