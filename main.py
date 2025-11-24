# -*- coding: utf-8 -*-
import keyboard
import time
import os
from inventory_detector import InventoryScanner
import config

# Log-Datei zurücksetzen
if os.path.exists(config.LOG_FILE):
    try:
        os.remove(config.LOG_FILE)
    except:
        pass
if os.path.exists(config.OUTPUT_FILE):
    try:
        os.remove(config.OUTPUT_FILE)
    except:
        pass

def log_print(*args, **kwargs):
    msg = " ".join(map(str, args))
    print(msg, **kwargs)
    try:
        with open(config.LOG_FILE, "a", encoding="utf-8", buffering=1) as f:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

def main():
    log_print("\n=== InvDetect – Star Citizen Universal Inventory Scanner ===")
    log_print("INSERT → Start | ESC → Sofort stoppen\n")
    log_print("Warte auf INSERT...")

    keyboard.wait('insert')

    log_print("\nSCAN GESTARTET – jetzt mit 101px Drag-Scroll und Datenbank-Korrektur!\n")
    scanner = InventoryScanner()

    try:
        scanner.scan_all_tiles()
        log_print("\nSCAN FERTIG! Siehe detected_items.txt")
    except KeyboardInterrupt:
        log_print("\nScan durch ESC abgebrochen.")
    except Exception as e:
        log_print(f"\nUNERWARTETER FEHLER: {e}")

    input("\nEnter zum Beenden...")

if __name__ == "__main__":
    main()