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

def debug_hover_and_scroll():
    """DEBUG: Kacheln abgehen und scrollen OHNE OCR/Datenbank"""
    log_print("\n=== DEBUG MODE: Hover + Scroll (KEIN OCR) ===")
    log_print("Geht alle Kacheln ab, hovert und scrollt - ohne OCR-Scan\n")

    # Config neu laden
    import importlib
    importlib.reload(config)

    scanner = InventoryScanner()
    scanner.scan_active = True

    try:
        # Erst nach oben scrollen
        scanner.reset_to_top()

        empty_blocks = 0

        # PHASE 1: Von oben nach unten
        while empty_blocks < 4 and scanner.scan_active:
            scanner.check_abort()

            log_print(f"\n=== DEBUG BLOCK {scanner.block_counter + 1} ===")

            # Basis-Y berechnen
            base_y = config.START_Y + config.FIRST_ROW_Y_OFFSET
            drift_val = int(config.DRIFT_COMPENSATION_PER_BLOCK)
            drift_correction = int(scanner.block_counter * drift_val)
            base_y -= drift_correction

            # Row offsets
            try:
                row_offsets = [i * config.ROW_STEP for i in range(8)]
            except AttributeError:
                row_offsets = [i * 97 for i in range(8)]

            # 8 Reihen durchgehen
            for row_idx, offset in enumerate(row_offsets):
                scanner.check_abort()
                row_y = base_y + offset

                if row_y < 0:
                    continue

                log_print(f"  Reihe {row_idx}: Y={row_y}")

                # 4 Spalten durchgehen
                for col in range(config.MAX_COLUMNS):
                    scanner.check_abort()

                    x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
                    y = row_y

                    # Nur hovern (kein OCR!)
                    pyautogui.moveTo(x, y, duration=0.02)

                    # Kurze Wiggle-Bewegung
                    scanner.check_abort()
                    pyautogui.moveRel(0, -3, duration=0.02)
                    time.sleep(0.05)
                    scanner.check_abort()
                    pyautogui.moveRel(0, 3, duration=0.02)
                    time.sleep(0.1)  # Kurz warten damit Tooltip sichtbar ist

                pyautogui.moveTo(100, 100, duration=0)  # Maus weg

            # Scroll nach unten
            log_print("\n  → Scrolle nach unten...")
            scroll_result = scanner.precise_scroll_down_once()

            if scroll_result == "END":
                log_print("\n[DEBUG] Scrollbalken-Ende erkannt! Starte Reverse-Scan...")

                # PHASE 2: Reverse-Scan von unten nach oben
                reverse_blocks = 0
                while reverse_blocks < 10 and scanner.scan_active:  # Max 10 Reverse-Blöcke
                    scanner.check_abort()

                    log_print(f"\n=== DEBUG REVERSE BLOCK {scanner.block_counter + 1} ===")

                    # Basis-Y von UNTEN berechnen
                    base_y = config.INVENTORY_BOTTOM - config.BORDER_OFFSET_TOP - (config.TILE_HEIGHT // 2) - 4
                    log_print(f"  [REVERSE] Starte von unten bei Y={base_y}")

                    # Row offsets negativ (von unten nach oben)
                    try:
                        row_offsets = [-i * config.ROW_STEP for i in reversed(range(8))]
                    except AttributeError:
                        row_offsets = [-i * 97 for i in reversed(range(8))]

                    # 8 Reihen durchgehen (von unten nach oben)
                    for row_idx, offset in enumerate(row_offsets):
                        scanner.check_abort()
                        row_y = base_y + offset

                        if row_y < 0:
                            continue

                        log_print(f"  Reihe {row_idx}: Y={row_y}")

                        # 4 Spalten durchgehen
                        for col in range(config.MAX_COLUMNS):
                            scanner.check_abort()

                            x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
                            y = row_y

                            # Nur hovern (kein OCR!)
                            pyautogui.moveTo(x, y, duration=0.02)

                            # Kurze Wiggle-Bewegung
                            scanner.check_abort()
                            pyautogui.moveRel(0, -3, duration=0.02)
                            time.sleep(0.05)
                            scanner.check_abort()
                            pyautogui.moveRel(0, 3, duration=0.02)
                            time.sleep(0.1)

                        pyautogui.moveTo(100, 100, duration=0)

                    # Scroll nach oben
                    log_print("\n  → Scrolle nach oben...")
                    scroll_result = scanner.precise_scroll_up_once()

                    if scroll_result == "TOP":
                        log_print("\n[DEBUG] Scrollbalken am Anfang erkannt! Reverse-Scan beendet.")
                        break

                    reverse_blocks += 1

                break

            empty_blocks = 0  # Reset da wir nicht auf leere Kacheln prüfen

        log_print("\n[DEBUG] Hover-Test beendet.")
        pyautogui.moveTo(100, 100, duration=0)

    except (KeyboardInterrupt, ScanAbortedException):
        log_print("\n[DEBUG] Hover-Test abgebrochen (ENTF gedrückt).")
    except Exception as e:
        log_print(f"\n[DEBUG] FEHLER: {e}")
        import traceback
        log_print(traceback.format_exc())
    finally:
        scanner.scan_active = False
        pyautogui.moveTo(100, 100, duration=0)

def main():
    log_print("\n=== InvDetect – Star Citizen Universal Inventory Scanner ===")
    log_print("INSERT → Start Scan | Q → Debug Hover (ohne OCR) | ENTF → Stoppen\n")

    first_run = True
    mode = None  # 'scan' oder 'debug'

    while True:
        if first_run:
            log_print("\nWarte auf INSERT (Scan) oder Q (Debug Hover ohne OCR)...")
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
            log_print("\nDrücke INSERT (Scan) oder Q (Debug Hover ohne OCR) zum Fortfahren...")
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
            debug_hover_and_scroll()
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