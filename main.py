# -*- coding: utf-8 -*-
"""
InvDetect - Star Citizen Inventar Scanner
Hauptprogramm

Drücke EINFÜGEN-Taste im Spiel = Scan startet
Drücke ESC = Programm beenden
"""

import keyboard
import time
import sys
from inventory_detector import InventoryScanner
import config


def on_scan_trigger():
    """
    Wird aufgerufen wenn EINFÜGEN gedrückt wird
    """
    print("\n" + "="*50)
    print("🎯 EINFÜGEN erkannt - Starte Scan!")
    print("="*50)
    
    # Scanner erstellen
    scanner = InventoryScanner()
    
    # Kurz warten (damit Spiel bereit ist)
    time.sleep(0.5)
    
    # Alle Kacheln scannen
    items = scanner.scan_all_tiles()
    
    # In Datei speichern
    scanner.save_to_file()
    
    print("\n" + "="*50)
    print(f"✅ FERTIG! {len(items)} Items gefunden")
    print("="*50 + "\n")


def main():
    """
    Hauptfunktion - wartet auf Tastendruck
    """
    print("\n")
    print("╔════════════════════════════════════════════╗")
    print("║   InvDetect - Star Citizen Scanner        ║")
    print("║   v1.0                                    ║")
    print("╚════════════════════════════════════════════╝")
    print("\n")
    
    print("⚙️  Einstellungen:")
    print(f"   • Hotkey: {config.TRIGGER_KEY.upper()}")
    print(f"   • Tesseract: {config.TESSERACT_PATH}")
    print(f"   • Output: {config.OUTPUT_FILE}")
    print("\n")
    
    print("📋 Anleitung:")
    print("   1. Starte Star Citizen")
    print("   2. Öffne dein Inventar")
    print("   3. Drücke EINFÜGEN-Taste")
    print("   4. Programm scannt automatisch")
    print("\n")
    
    print("⌨️  Steuerung:")
    print(f"   • {config.TRIGGER_KEY.upper()} = Scan starten")
    print("   • ESC = Programm beenden")
    print("\n")
    
    print("⏳ Warte auf Eingabe...\n")
    
    # Hotkey registrieren
    keyboard.add_hotkey(config.TRIGGER_KEY, on_scan_trigger)
    
    # Auf ESC warten zum Beenden
    try:
        keyboard.wait('esc')
    except KeyboardInterrupt:
        pass
    
    print("\n👋 Programm beendet.\n")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fehler: {e}\n")
        input("Drücke Enter zum Beenden...")
        sys.exit(1)
