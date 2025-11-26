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
    """DEBUG: Kacheln abgehen und scrollen OHNE OCR/Datenbank - MIT Button-Check Schleife"""
    log_print("\n=== DEBUG MODE: Hover + Scroll (KEIN OCR) + Button-Check ===")
    log_print("3 Blöcke + kleiner Scroll + letzte Reihe + Button-Check-Schleife\n")

    # Config neu laden
    import importlib
    importlib.reload(config)

    scanner = InventoryScanner()
    scanner.scan_active = True
    scan_iteration = 0  # Zähler für Durchläufe

    try:
        # Erst nach oben scrollen
        scanner.reset_to_top()

        # Hauptschleife: Wiederhole bis Button inaktiv
        while scanner.scan_active:
            scan_iteration += 1
            log_print(f"\n{'='*80}")
            log_print(f"DEBUG DURCHLAUF #{scan_iteration}")
            log_print(f"{'='*80}\n")

            # Scanne 3 Blöcke (je 8 Reihen)
            for block_num in range(3):
                scanner.check_abort()

                log_print(f"\n=== DEBUG BLOCK {scanner.block_counter + 1} ===")

                # Basis-Y berechnen
                base_y = config.START_Y + config.FIRST_ROW_Y_OFFSET
                drift_val = int(config.DRIFT_COMPENSATION_PER_BLOCK)
                drift_correction = int(scanner.block_counter * drift_val)
                base_y -= drift_correction
                log_print(f"  Block {scanner.block_counter + 1} → Y-Korrektur: -{drift_correction}px → erste Reihe bei y={base_y}")

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
                        log_print(f"  [ACHTUNG] Y-Koordinate {row_y} ist < 0! Übersprungen.")
                        continue

                    log_print(f"  Reihe {row_idx + 1}: Y={row_y}")

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

                # Nach Block 1 und 2 scrollen (nicht nach Block 3)
                if block_num < 2:
                    log_print("\n  → Scrolle nach unten...")
                    scanner.check_abort()
                    scanner.precise_scroll_down_once()

            # Nach 3 Blöcken: Kleiner Scroll für 1 Reihe
            log_print("\n→ Kleiner Scroll zur letzten Reihe...")
            scanner.check_abort()

            cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
            cy = config.SCROLL_AREA_BOTTOM - 100

            small_scroll = config.SCROLL_PIXELS_UP // 8  # 322 / 8 = 40px
            log_print(f"  Scrolle {small_scroll}px nach unten (für 1 Reihe)")

            pyautogui.moveTo(cx, cy, duration=0)
            pyautogui.drag(0, small_scroll, duration=0.2, button='left')
            time.sleep(0.3)

            # Scanne nur die letzte Reihe (Reihe 25 bei Y=974)
            log_print("\n=== DEBUG: LETZTE REIHE (25) ===")

            # Berechne Y-Position
            row_25_y = config.INVENTORY_BOTTOM - config.BORDER_OFFSET_TOP - (config.TILE_HEIGHT // 2)
            log_print(f"  Reihe 25: Y={row_25_y}")

            for col in range(config.MAX_COLUMNS):
                scanner.check_abort()

                x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)

                # Nur hovern (kein OCR!)
                pyautogui.moveTo(x, row_25_y, duration=0.02)

                # Kurze Wiggle-Bewegung
                scanner.check_abort()
                pyautogui.moveRel(0, -3, duration=0.02)
                time.sleep(0.05)
                scanner.check_abort()
                pyautogui.moveRel(0, 3, duration=0.02)
                time.sleep(0.1)

            pyautogui.moveTo(100, 100, duration=0)

            # Button-Check nach letzter Reihe
            log_print("\n→ Prüfe Button-Status...")
            scanner.check_abort()
            button_active = scanner.check_button_brightness()

            if button_active:
                log_print("[DEBUG] Button aktiv - klicke und starte neuen Durchlauf")
                button_center_x = 1612
                button_center_y = 1040
                pyautogui.click(button_center_x, button_center_y)
                log_print(f"  Button geklickt bei ({button_center_x}, {button_center_y})")
                # Warte 5 Sekunden (Inventar muss sich aufbauen)
                log_print("  Warte 5 Sekunden (Inventar lädt)...")
                for _ in range(50):  # 50 * 0.1s = 5s
                    scanner.check_abort()
                    time.sleep(0.1)
                # Reset für nächsten Durchlauf
                scanner.reset_to_top()
                log_print("  Bereit für nächsten Debug-Durchlauf\n")
            else:
                log_print("[DEBUG] Button inaktiv - Schleife beendet")
                break  # Beende die while-Schleife

        log_print("\n[DEBUG] Hover-Test mit Button-Check abgeschlossen.")
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