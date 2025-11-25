# -*- coding: utf-8 -*-
"""
inventory_detector.py – FINAL VERSION
Implementiert: 
1. Korrekte 97px Zeilenverschiebung.
2. Stabile Drift-Kompensation (z.B. 16px).
3. Robustes Scrollen durch Farbsuche des variablen Scrollbalkens.
4. Korrigierte Scroll-Richtung (Ziehen nach unten = Inhalt scrollt nach unten).
"""

import pyautogui
import time
import config
import ocr_scanner
import keyboard
import os 

def log_print(*args, **kwargs):
    msg = " ".join(map(str, args))
    print(msg, **kwargs)
    try:
        # Sicherstellen, dass die Log-Datei aus config gelesen und geschrieben wird
        with open(config.LOG_FILE, "a", encoding="utf-8", buffering=1) as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except:
        pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01  # schnelleres Ausführen

class ScanAbortedException(Exception):
    """Custom Exception für ESC-Abbruch"""
    pass

class InventoryScanner:
    def __init__(self):
        self.detected_items = set()
        self.block_counter = 0   # wird erst NACH dem Scrollen erhöht → korrekt!
        self.scan_active = False  # Flag für aktiven Scan

    def check_abort(self):
        """Prüft ob ENTF gedrückt wurde und wirft Exception"""
        if keyboard.is_pressed('delete'):
            self.scan_active = False
            import traceback
            # Debug: Zeige wo der Abbruch stattfindet
            stack = traceback.extract_stack()
            caller = stack[-2]  # Die aufrufende Funktion
            log_print(f"\n[ABBRUCH] ENTF gedrückt bei {caller.name}:{caller.lineno}")
            raise ScanAbortedException("ENTF gedrückt")

    def reset_to_top(self):
        log_print("Komplett nach oben scrollen...")
        # Maus auf Inventar-Mitte setzen, um Scroll-Events zu empfangen
        cx = (config.INVENTORY_LEFT + config.INVENTORY_RIGHT) // 2
        cy = config.INVENTORY_BOTTOM - 50
        pyautogui.moveTo(cx, cy, duration=0)  # Instant
        # 40 Scrolls nach oben, um sicher ganz oben zu sein
        for i in range(40):
            self.check_abort()
            pyautogui.scroll(1200)
            time.sleep(0.04)

        # 1.5s Wartezeit aufteilen für bessere Responsiveness
        for _ in range(15):
            self.check_abort()
            time.sleep(0.1)

        self.block_counter = 0
        log_print("Zurück am Anfang – Drift-Reset")

    def precise_scroll_down_once(self):
        self.check_abort()

        log_print("  Suche nach größter Scrollbalken-Fläche...")

        # 1. Screenshot der Scroll-Region machen
        scroll_shot = pyautogui.screenshot(region=(
            config.SCROLL_AREA_LEFT,
            config.SCROLL_AREA_TOP,
            config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT,
            config.SCROLL_AREA_BOTTOM - config.SCROLL_AREA_TOP
        ))

        # 2. Finde alle Pixel mit Scrollbalken-Farbe und größte zusammenhängende Fläche
        import numpy as np
        img_array = np.array(scroll_shot)

        # Maske für Scrollbalken-Farbe erstellen
        target_color = np.array(config.SCROLLBAR_COLOR)
        tolerance = config.SCROLL_COLOR_TOLERANCE

        # Berechne Distanz jedes Pixels zur Zielfarbe
        color_diff = np.abs(img_array - target_color)
        matches = np.all(color_diff <= tolerance, axis=2)

        # Finde Y-Koordinaten aller passenden Pixel in der mittleren X-Spalte
        mid_x = (config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT) // 2
        matching_ys = np.where(matches[:, mid_x])[0]

        found_y = -1
        if len(matching_ys) > 0:
            # Finde größte zusammenhängende Gruppe (Scrollbalken)
            groups = []
            current_group = [matching_ys[0]]

            for i in range(1, len(matching_ys)):
                if matching_ys[i] - matching_ys[i-1] <= 2:  # Max 2px Lücke
                    current_group.append(matching_ys[i])
                else:
                    groups.append(current_group)
                    current_group = [matching_ys[i]]
            groups.append(current_group)

            # Größte Gruppe = Scrollbalken
            largest_group = max(groups, key=len)
            if len(largest_group) >= 10:  # Mindestens 10px hoch
                # Mitte der größten Gruppe
                found_y = int(np.mean(largest_group))
                log_print(f"  Scrollbalken gefunden: Y={found_y + config.SCROLL_AREA_TOP}, Höhe={len(largest_group)}px")
            else:
                log_print(f"  [WARNUNG] Scrollbalken zu klein: {len(largest_group)}px")

        # 3. Bestimme den finalen Drag-Startpunkt
        if found_y == -1:
            log_print("  [WARNUNG] Scrollbalken-Fläche nicht gefunden. Nutze Fallback.")
            cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
            cy = config.SCROLL_AREA_BOTTOM - 50
        else:
            # Erfolgreich: Absolute Koordinaten
            cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
            cy = found_y + config.SCROLL_AREA_TOP

        log_print(f"  Starte Drag von X={cx}, Y={cy}, Distanz={config.SCROLL_PIXELS_UP}px")

        # 4. Maus zum Startpunkt bewegen
        self.check_abort()
        pyautogui.moveTo(cx, cy, duration=0.05)
        time.sleep(0.1)  # Kurz warten

        # 5. Drag mit tatsächlicher Duration (duration=0 funktioniert nicht zuverlässig für drag!)
        self.check_abort()
        pyautogui.drag(0, config.SCROLL_PIXELS_UP, duration=0.3, button='left')

        # Wartezeit nach Scroll aufteilen für bessere Responsiveness
        wait_steps = 8
        for _ in range(wait_steps):
            self.check_abort()
            time.sleep(config.SCROLL_WAIT / wait_steps)

        self.block_counter += 1
        log_print(f"  Gescrollt. Block-Zähler: {self.block_counter}")


    def scan_8_rows_block(self):
        found = 0

        # 1. Basis-Y berechnen (Startpunkt + Offset für die Mitte der ersten Reihe)
        base_y = config.START_Y + config.FIRST_ROW_Y_OFFSET

        # 2. Drift-Kompensation berechnen und anwenden (Maus bewegt sich nach oben)
        drift_val = int(config.DRIFT_COMPENSATION_PER_BLOCK)
        drift_correction = int(self.block_counter * drift_val)
        base_y -= drift_correction

        # DEBUG: Zeige detaillierte Y-Position Berechnung
        expected_y = config.START_Y + config.FIRST_ROW_Y_OFFSET
        log_print(f"  [DEBUG] Block {self.block_counter + 1}:")
        log_print(f"    START_Y={config.START_Y}, FIRST_ROW_Y_OFFSET={config.FIRST_ROW_Y_OFFSET}")
        log_print(f"    Erwartete Y-Position (ohne Drift): {expected_y}")
        log_print(f"    Drift-Korrektur: -{drift_correction}px (block_counter={self.block_counter}, drift_val={drift_val})")
        log_print(f"    Finale base_y: {base_y}")
        log_print(f"    Differenz zum Soll: {base_y - expected_y}px")

        # 3. Dynamische row_offsets verwenden (FIX für 97px Zeilenabstand)
        try:
            row_offsets = [i * config.ROW_STEP for i in range(8)]
        except AttributeError:
            log_print("FEHLER: config.ROW_STEP nicht gefunden! Nutze Fallback 97px.")
            row_offsets = [i * 97 for i in range(8)]


        for offset in row_offsets:
            self.check_abort()
            row_y = base_y + offset

            # Sicherheitscheck: verhindert Abstürze durch negative Y-Koordinaten
            if row_y < 0:
                log_print(f"  [ACHTUNG] Y-Koordinate {row_y} ist < 0! Scan übersprungen.")
                continue

            for col in range(config.MAX_COLUMNS):
                self.check_abort()

                # X-Koordinate berechnen
                x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
                y = row_y

                # Sehr kurze Bewegung (20ms), damit Spiel Maus-Event erkennt
                pyautogui.moveTo(x, y, duration=0.02)

                # Wiggle: Kurz hoch und runter bewegen, um Tooltip zu triggern
                self.check_abort()
                pyautogui.moveRel(0, -3, duration=0.02)  # 3px hoch
                time.sleep(0.05)
                self.check_abort()
                pyautogui.moveRel(0, 3, duration=0.02)   # 3px runter (zurück)

                # Während der Wartezeit mehrfach prüfen
                for _ in range(8):
                    self.check_abort()
                    time.sleep(0.025)  # 8 x 0.025 = 0.2s (reduziert wegen Wiggle)

                # Screenshot des OCR-Bereichs
                self.check_abort()
                shot = pyautogui.screenshot(region=(
                    config.OCR_LEFT, config.OCR_TOP,
                    config.OCR_WIDTH, config.OCR_HEIGHT
                ))

                text = ocr_scanner.scan_image_for_text(shot).strip()

                # WICHTIG: Check direkt nach OCR, da OCR lange dauert (100-300ms)
                self.check_abort()

                pyautogui.moveTo(100, 100, duration=0)  # Maus instant aus dem Weg

                if text and text not in self.detected_items:
                    log_print(f"  → {text}")
                    self.detected_items.add(text)
                    with open(config.OUTPUT_FILE, 'a', encoding='utf-8') as f:
                        f.write(text + '\n')
                    found += 1

        return found > 0

    def scan_all_tiles(self):
        log_print("\n" + "="*80)
        log_print(f"SCAN GESTARTET – Drift pro Block: {config.DRIFT_COMPENSATION_PER_BLOCK}px")
        log_print(f"X-Offset: {config.HOVER_OFFSET_X}px | Zeilenschritt: {getattr(config, 'ROW_STEP', 'NICHT GESETZT')}px")
        log_print("="*80 + "\n")

        self.scan_active = True

        try:
            self.reset_to_top()
            empty_blocks = 0

            while empty_blocks < 4 and self.scan_active:
                self.check_abort()

                log_print(f"\n=== BLOCK {self.block_counter + 1} WIRD GESCANNT ===")

                if self.scan_8_rows_block():
                    empty_blocks = 0
                else:
                    empty_blocks += 1
                    log_print(f"  Leerer Block ({empty_blocks}/4)")

                if empty_blocks < 4:
                    self.precise_scroll_down_once()

            log_print("\nScan beendet, da 4 leere Blöcke gefunden wurden.")

        except ScanAbortedException:
            # Normal handling für ESC-Abbruch
            pass

        finally:
            # Bei Abbruch: Maus in neutrale Position bewegen
            self.scan_active = False
            pyautogui.moveTo(100, 100, duration=0)  # Instant
            log_print("Maus gestoppt und in Ruheposition bewegt.")