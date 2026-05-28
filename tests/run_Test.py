import subprocess
import sys
from datetime import datetime

def run_tests():
    """Führt Tests aus ohne HTML-Report"""
    
    print("=" * 70)
    print("🧪 TO-DO-LISTEN TEST SUITE")
    print("=" * 70)
    print(f"Startzeit: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print()
    
    # Prüfe Abhängigkeiten
    try:
        import pytest
    except ImportError:
        print("❌ pytest nicht installiert!")
        print("Installation: pip install pytest")
        sys.exit(1)
    
    print("📋 Führe Tests aus...\n")
    
    # Führe Tests aus OHNE HTML-Report
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_todo.py", "-v", "--tb=short"],
        text=True
    )
    
    print("\n" + "=" * 70)
    
    if result.returncode == 0:
        print("✅ ALLE TESTS BESTANDEN!")
    else:
        print("❌ EINIGE TESTS FEHLGESCHLAGEN!")
    
    print("=" * 70)
    print(f"Endzeit: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    return result.returncode
    

if __name__ == "__main__":
    sys.exit(run_tests())