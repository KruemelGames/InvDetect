# -*- coding: utf-8 -*-
import keyboard
import time
import sys
import os
from inventory_detector import InventoryScanner
import config

LOG_FILE = "scan_log.txt"
if os.path.exists(LOG_FILE):
    try: os.remove(LOG_FILE)
    except: pass

def log_print(*args, **kwargs):
    msg = " ".join(map(str, args))
    print(msg, **kwargs)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except: pass

def main():
    log_print("\nInvDetect – Star Citizen Helm-Scanner FINAL\n")
    log_print("INSERT → Start | ESC → Sofort stoppen\n")

    try:
        open(config.OUTPUT_FILE, 'w', encoding='utf-8').close()
        log_print(f"{config.OUTPUT_FILE} geleert\n")
    except: pass

    log_print("Warte auf INSERT...")
    keyboard.wait('insert')

    log_print("\nSCAN GESTARTET – ESC zum Abbrechen!\n")
    scanner = InventoryScanner()

    try:
        scanner.scan_all_tiles()
        log_print("\nSCAN FERTIG! Siehe detected_items.txt und scan_log.txt")
    except KeyboardInterrupt:
        log_print("\nScan vom User abgebrochen.")
    except Exception as e:
        log_print(f"\nFehler: {e}")

    input("\nEnter zum Beenden...")

if __name__ == "__main__":
    main()