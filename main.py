# -*- coding: utf-8 -*-
import keyboard
import time
import os
from inventory_detector import InventoryScanner, ScanAbortedException
import config
import pyautogui

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

def debug_scroll_only():
    """DEBUG: Ein Scroll durchführen und Drift-Position anzeigen"""
    log_print("\n=== DEBUG SCROLL ===")

    # Config neu laden
    import importlib
    importlib.reload(config)
    log_print(f"[DEBUG] SCROLL_PIXELS_UP = {config.SCROLL_PIXELS_UP}")
    log_print(f"[DEBUG] DRIFT_COMPENSATION_PER_BLOCK = {config.DRIFT_COMPENSATION_PER_BLOCK}")

    scanner = InventoryScanner()

    try:
        # Erst nach oben scrollen
        scanner.reset_to_top()

        # Ein Scroll durchführen
        log_print("\n[DEBUG] Führe einen Scroll durch...")
        scanner.precise_scroll_down_once()
        log_print(f"[DEBUG] Scroll fertig! Block-Counter: {scanner.block_counter}")

        # Jetzt zeigen wo die erste Reihe nach dem Scroll sein sollte
        base_y = config.START_Y + config.FIRST_ROW_Y_OFFSET
        drift_correction = scanner.block_counter * config.DRIFT_COMPENSATION_PER_BLOCK
        adjusted_y = base_y - drift_correction
        x = config.START_X + config.HOVER_OFFSET_X

        log_print(f"\n[DEBUG] Berechnung der ersten Reihe:")
        log_print(f"  START_Y = {config.START_Y}")
        log_print(f"  FIRST_ROW_Y_OFFSET = {config.FIRST_ROW_Y_OFFSET}")
        log_print(f"  base_y (ohne Drift) = {base_y}")
        log_print(f"  drift_correction = {drift_correction}px")
        log_print(f"  adjusted_y (mit Drift) = {adjusted_y}")

        # Maus zur berechneten Position bewegen
        log_print(f"\n[DEBUG] Bewege Maus zur ersten Reihe: X={x}, Y={adjusted_y}")
        pyautogui.moveTo(x, adjusted_y, duration=0.5)

        log_print("[DEBUG] Prüfe jetzt visuell: Ist die Maus auf der ersten Tile-Reihe?\n")

    except (KeyboardInterrupt, ScanAbortedException):
        log_print("\n[DEBUG] Scroll-Test abgebrochen.")
    except Exception as e:
        log_print(f"\n[DEBUG] FEHLER: {e}")
        import traceback
        log_print(traceback.format_exc())

def main():
    log_print("\n=== InvDetect – Star Citizen Universal Inventory Scanner ===")
    log_print("INSERT → Start Scan | Q → Debug Scroll | ENTF → Stoppen\n")

    first_run = True
    mode = None  # 'scan' oder 'debug'

    while True:
        if first_run:
            log_print("\nWarte auf INSERT (Scan) oder Q (Debug Scroll)...")
            # Warte auf INSERT oder Q
            while True:
                if keyboard.is_pressed('insert'):
                    mode = 'scan'
                    break
                elif keyboard.is_pressed('q'):
                    mode = 'debug'
                    break
                time.sleep(0.05)

            first_run = False
            time.sleep(0.3)  # Entprellen
        else:
            # Nach Abbruch: Frage welcher Modus
            log_print("\nDrücke INSERT (Scan) oder Q (Debug Scroll) zum Fortfahren...")
            while True:
                if keyboard.is_pressed('insert'):
                    mode = 'scan'
                    break
                elif keyboard.is_pressed('q'):
                    mode = 'debug'
                    break
                time.sleep(0.05)
            time.sleep(0.3)  # Entprellen

        # DEBUG MODUS
        if mode == 'debug':
            debug_scroll_only()
            continue

        # NORMALER SCAN MODUS
        # Config neu laden für on-the-fly Änderungen
        import importlib
        importlib.reload(config)
        log_print("[INFO] Config neu geladen")

        log_print("\nSCAN GESTARTET – jetzt mit 101px Drag-Scroll und Datenbank-Korrektur!\n")
        scanner = InventoryScanner()

        try:
            scanner.scan_all_tiles()
            log_print("\nSCAN FERTIG! Siehe detected_items.txt")
            log_print(f"Insgesamt {len(scanner.detected_items)} unterschiedliche Items gefunden.")

            # Nach erfolgreichem Scan: Frage ob nochmal
            log_print("\nDrücke ENTER für einen weiteren Scan oder schließe das Fenster zum Beenden.")
            input()
            # Loop läuft weiter für weiteren Scan

        except (KeyboardInterrupt, ScanAbortedException):
            log_print("\n>>> Scan durch ENTF abgebrochen. <<<")
            # Loop läuft weiter, wartet auf ENTER

        except pyautogui.FailSafeException:
            log_print("\n>>> PyAutoGUI Fail-Safe ausgelöst (Maus in Bildschirmecke) <<<")
            log_print("Das passiert, wenn die Maus in eine Ecke bewegt wird.")
            # Loop läuft weiter, wartet auf ENTER

        except Exception as e:
            log_print(f"\nUNERWARTETER FEHLER: {e}")
            import traceback
            log_print(traceback.format_exc())
            break  # Bei echtem Fehler beenden

if __name__ == "__main__":
    main()