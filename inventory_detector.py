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
from collections import Counter 

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
        self.detected_items = Counter()  # Counter statt set() für Duplikat-Zählung
        self.block_counter = 0   # wird erst NACH dem Scrollen erhöht → korrekt!
        self.scan_active = False  # Flag für aktiven Scan
        self.last_row_items = []  # Speichert Items der letzten Reihe vor Reverse-Scan

        # Erstelle Output-Datei beim Start, falls nicht vorhanden
        if not os.path.exists(config.OUTPUT_FILE):
            try:
                with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    f.write("# Inventory Scan Results\n")
                    f.write("# Format: Anzahl, Item-Name\n")
                    f.write("# Waiting for scan to complete...\n")
                log_print(f"[INFO] Output-Datei erstellt: {config.OUTPUT_FILE}")
            except Exception as e:
                log_print(f"[WARNUNG] Konnte Output-Datei nicht erstellen: {e}")

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

        # Maske für Scrollbalken-Farbe erstellen (beide Farben: normal und gehovert)
        tolerance = config.SCROLL_COLOR_TOLERANCE

        # Prüfe beide Farben
        color1 = np.array(config.SCROLLBAR_COLOR)  # Nicht gehovert
        color2 = np.array(config.SCROLLBAR_COLOR_HOVER)  # Gehovert

        # Berechne Distanz jedes Pixels zu beiden Zielfarben
        color_diff1 = np.abs(img_array - color1)
        matches1 = np.all(color_diff1 <= tolerance, axis=2)

        color_diff2 = np.abs(img_array - color2)
        matches2 = np.all(color_diff2 <= tolerance, axis=2)

        # Kombiniere beide Masken (ODER-Verknüpfung)
        matches = matches1 | matches2

        # Finde Y-Koordinaten aller passenden Pixel in der mittleren X-Spalte
        mid_x = (config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT) // 2
        matching_ys = np.where(matches[:, mid_x])[0]

        found_y = -1
        found_y_bottom = -1
        scrollbar_height = 0

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
                # Mitte und unteres Ende der größten Gruppe
                found_y = int(np.mean(largest_group))
                found_y_bottom = int(np.max(largest_group))  # Unteres Ende (relativ)
                scrollbar_height = len(largest_group)

                # Absolute Koordinaten berechnen
                absolute_y = found_y + config.SCROLL_AREA_TOP
                absolute_y_bottom = found_y_bottom + config.SCROLL_AREA_TOP

                log_print(f"  Scrollbalken gefunden: Mitte Y={absolute_y}, Unten Y={absolute_y_bottom}, Höhe={scrollbar_height}px")

                # Prüfe ob unteres Ende des Scrollbalkens im Ende-Bereich ist
                end_min = getattr(config, 'SCROLLBAR_END_MIN', 930)
                end_max = getattr(config, 'SCROLLBAR_END_MAX', 1021)
                log_print(f"  [SCROLLBAR CHECK] Unteres Ende Y={absolute_y_bottom} (Ziel-Bereich: {end_min}-{end_max})")
                if absolute_y_bottom >= end_min and absolute_y_bottom <= end_max:
                    log_print(f"  ✓ [SCROLLBAR-ENDE] Scrollbalken im Zielbereich erkannt! Y={absolute_y_bottom}")
                    return "END"  # Spezieller Rückgabewert für Ende
                else:
                    log_print(f"  → [SCROLLBAR] Noch nicht im Zielbereich (Differenz: {end_min - absolute_y_bottom}px)")
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

        # 4. Prüfe ob Drag den Scrollbalken aus dem Bereich ziehen würde
        drag_distance = config.SCROLL_PIXELS_UP
        target_y = cy + drag_distance
        # Erlaube bis knapp vor SCROLLBAR_END_MAX (damit Scrollbalken im Zielbereich landen kann)
        end_max = getattr(config, 'SCROLLBAR_END_MAX', 1021)
        max_y = end_max + 5  # 5px Puffer über dem Zielbereich

        if target_y > max_y:
            # Drag würde zu weit gehen - reduziere die Distanz
            adjusted_drag = max_y - cy
            log_print(f"  [WARNUNG] Drag würde Scrollbalken aus Bereich ziehen!")
            log_print(f"    Original: {drag_distance}px würde zu Y={target_y} führen (Max: {max_y})")
            log_print(f"    Angepasst: {adjusted_drag}px (Ziel Y={max_y})")
            drag_distance = adjusted_drag

        log_print(f"  Starte Drag von X={cx}, Y={cy}, Distanz={drag_distance}px")

        # 5. Maus zum Startpunkt bewegen und warten (für Hover-Effekt)
        self.check_abort()
        pyautogui.moveTo(cx, cy, duration=0.05)
        time.sleep(0.15)  # Erhöht von 0.1s auf 0.15s für Hover-Effekt

        # 6. Drag mit tatsächlicher Duration (duration=0 funktioniert nicht zuverlässig für drag!)
        self.check_abort()
        pyautogui.drag(0, drag_distance, duration=0.3, button='left')

        # Wartezeit nach Scroll aufteilen für bessere Responsiveness
        wait_steps = 8
        for _ in range(wait_steps):
            self.check_abort()
            time.sleep(config.SCROLL_WAIT / wait_steps)

        self.block_counter += 1
        log_print(f"  Gescrollt. Block-Zähler: {self.block_counter}")


    def scan_8_rows_block(self, reverse=False, check_partial_rows=True):
        """
        Scannt 8 Reihen eines Blocks.

        Args:
            reverse: Wenn True, wird von unten nach oben gescannt (Reihe 7 -> 0)
            check_partial_rows: Wenn True, prüft auf 2 aufeinanderfolgende leere Reihen (nur für Normal-Scan)

        Returns:
            bool oder "EMPTY_ROWS": True wenn Items gefunden, "EMPTY_ROWS" wenn 2 aufeinanderfolgende Reihen 0 Items haben
        """
        found = 0
        consecutive_empty_rows = 0  # Zähler für aufeinanderfolgende leere Reihen

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

        # Wenn reverse=True, kehre die Reihenfolge um (Reihe 7 -> 0)
        if reverse:
            row_offsets = list(reversed(row_offsets))
            log_print("  [REVERSE] Scanne von unten nach oben")

        for row_idx, offset in enumerate(row_offsets):
            self.check_abort()
            row_y = base_y + offset

            # Sicherheitscheck: verhindert Abstürze durch negative Y-Koordinaten
            if row_y < 0:
                log_print(f"  [ACHTUNG] Y-Koordinate {row_y} ist < 0! Scan übersprungen.")
                continue

            row_items_found = 0  # Zähle Items pro Reihe
            row_items = []  # Speichere Items dieser Reihe

            for col in range(config.MAX_COLUMNS):
                self.check_abort()

                # X-Koordinate berechnen
                x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
                y = row_y

                # Bis zu 5 Scan-Versuche, wenn nichts erkannt wird
                text = ""
                for attempt in range(1, 6):  # Versuche 1-5
                    self.check_abort()

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

                    # OCR gibt jetzt Tuple zurück: (korrigierter_text, roher_text, wurde_korrigiert)
                    scan_result = ocr_scanner.scan_image_for_text(shot)
                    text = scan_result[0].strip()
                    raw_ocr = scan_result[1]
                    was_corrected = scan_result[2]

                    # WICHTIG: Check direkt nach OCR, da OCR lange dauert (100-300ms)
                    self.check_abort()

                    if text:
                        # Text erkannt - fertig!
                        if attempt > 1:
                            log_print(f"    [RETRY] Text erkannt nach {attempt} Versuchen")
                        break
                    else:
                        # Kein Text - Retry wenn noch Versuche übrig
                        if attempt < 5:
                            if raw_ocr:
                                log_print(f"    [RETRY] Versuch {attempt}/5: Kein DB-Match für OCR-Text: '{raw_ocr}'")
                            else:
                                log_print(f"    [RETRY] Versuch {attempt}/5: Kein Text erkannt, versuche erneut...")
                        else:
                            if raw_ocr:
                                log_print(f"    [SCAN FAILED] OCR erkannte: '{raw_ocr}' - KEINE Übereinstimmung in Datenbank!")
                            else:
                                log_print(f"    [RETRY] Alle 5 Versuche fehlgeschlagen - Kachel leer")

                pyautogui.moveTo(100, 100, duration=0)  # Maus instant aus dem Weg

                if text:
                    self.detected_items[text] += 1  # Zählt jedes Item (auch Duplikate)
                    count = self.detected_items[text]
                    log_print(f"  → {text} (#{count})")
                    found += 1
                    row_items_found += 1
                    row_items.append(text)

            # Speichere letzte Reihe (Reihe 7 beim normalen Scan)
            if not reverse and row_idx == 7:
                self.last_row_items = row_items.copy()
                log_print(f"  [INFO] Letzte Reihe gespeichert: {self.last_row_items}")

            # Prüfe ob diese Reihe komplett leer ist (0 Items)
            if check_partial_rows and not reverse:
                if row_items_found == 0:
                    consecutive_empty_rows += 1
                    log_print(f"  [INFO] Leere Reihe {row_idx} ({consecutive_empty_rows} hintereinander)")

                    # Wenn 2 aufeinanderfolgende leere Reihen → STOPP
                    if consecutive_empty_rows >= 2:
                        log_print(f"  [INFO] 2 leere Reihen hintereinander → Prüfe Scrollbalken-Ende")
                        return "EMPTY_ROWS"
                else:
                    # Reset wenn eine volle Reihe gefunden wurde
                    consecutive_empty_rows = 0

        return found > 0

    def scan_from_bottom_up(self):
        """
        Scannt von unten nach oben und stoppt, wenn die letzten 4 Items Duplikate sind.
        """
        log_print("\n" + "="*80)
        log_print("REVERSE SCAN: Von unten nach oben")
        log_print("="*80 + "\n")

        # Liste der letzten gescannten Items (für Duplikat-Erkennung)
        # Starte mit der gespeicherten letzten Reihe vom Normal-Scan
        last_scanned = self.last_row_items.copy()

        if last_scanned:
            log_print(f"[INFO] Starte mit gespeicherter letzter Reihe: {last_scanned}")

        while self.scan_active:
            self.check_abort()

            log_print(f"\n=== REVERSE BLOCK {self.block_counter + 1} ===")

            # Scanne Block von unten nach oben (reverse=True)
            items_in_block = self.scan_8_rows_block_with_tracking(reverse=True)

            # Füge die Items zur last_scanned Liste hinzu
            last_scanned.extend(items_in_block)

            # Prüfe ob die letzten 4 Items Duplikate sind
            if len(last_scanned) >= 4:
                last_4 = last_scanned[-4:]
                log_print(f"\n[DEBUG] Letzte 4 Items: {last_4}")

                # Prüfe ob alle 4 Items bereits vorher gescannt wurden (Duplikate)
                # Ein Item ist Duplikat wenn detected_items[item] > 1
                duplicates = [item for item in last_4 if self.detected_items.get(item, 0) > 1]

                if len(duplicates) == 4:
                    log_print(f"\n[INFO] 4 Duplikate in Folge erkannt: {last_4}")
                    log_print("[INFO] Reverse Scan beendet!")
                    break

            # Scroll nach oben (negatives Scrollen)
            scroll_result = self.precise_scroll_up_once()

            # Prüfe ob Scrollbalken ganz oben ist
            if scroll_result == "TOP":
                log_print("\n[INFO] Scrollbalken am Anfang erkannt! Scan beendet.")
                break

    def scan_8_rows_block_with_tracking(self, reverse=False):
        """
        Scannt 8 Reihen und gibt die gefundenen Items zurück.
        WICHTIG: Diese Funktion stoppt NICHT bei 1-3 leeren Kacheln (für Reverse-Scan).

        Returns:
            List[str]: Liste der gefundenen Item-Namen
        """
        found_items = []

        # 1. Basis-Y berechnen
        if reverse:
            # Bei Reverse-Scan von UNTEN starten
            # INVENTORY_BOTTOM (1021) - 4px Spacing - 43px zur Tile-Mitte ≈ 974
            base_y = config.INVENTORY_BOTTOM - config.BORDER_OFFSET_TOP - (config.TILE_HEIGHT // 2) - 4
            log_print(f"  [REVERSE] Starte von unten bei Y={base_y}")
        else:
            # Normal-Scan von OBEN
            base_y = config.START_Y + config.FIRST_ROW_Y_OFFSET

        # 2. Drift-Kompensation (nur bei Normal-Scan)
        if not reverse:
            drift_val = int(config.DRIFT_COMPENSATION_PER_BLOCK)
            drift_correction = int(self.block_counter * drift_val)
            base_y -= drift_correction

        # 3. Row offsets
        try:
            row_offsets = [i * config.ROW_STEP for i in range(8)]
        except AttributeError:
            row_offsets = [i * 97 for i in range(8)]

        # Reverse: von unten nach oben bedeutet negative Offsets
        if reverse:
            row_offsets = [-offset for offset in reversed(row_offsets)]
            log_print("  [REVERSE] Scanne von unten nach oben")

        for row_idx, offset in enumerate(row_offsets):
            self.check_abort()
            row_y = base_y + offset

            if row_y < 0:
                continue

            row_items = []  # Items dieser Reihe

            for col in range(config.MAX_COLUMNS):
                self.check_abort()

                x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
                y = row_y

                # Bis zu 5 Scan-Versuche, wenn nichts erkannt wird
                text = ""
                for attempt in range(1, 6):  # Versuche 1-5
                    self.check_abort()

                    pyautogui.moveTo(x, y, duration=0.02)

                    # Wiggle
                    self.check_abort()
                    pyautogui.moveRel(0, -3, duration=0.02)
                    time.sleep(0.05)
                    self.check_abort()
                    pyautogui.moveRel(0, 3, duration=0.02)

                    for _ in range(8):
                        self.check_abort()
                        time.sleep(0.025)

                    # Screenshot
                    self.check_abort()
                    shot = pyautogui.screenshot(region=(
                        config.OCR_LEFT, config.OCR_TOP,
                        config.OCR_WIDTH, config.OCR_HEIGHT
                    ))

                    # OCR gibt jetzt Tuple zurück: (korrigierter_text, roher_text, wurde_korrigiert)
                    scan_result = ocr_scanner.scan_image_for_text(shot)
                    text = scan_result[0].strip()
                    raw_ocr = scan_result[1]
                    was_corrected = scan_result[2]
                    self.check_abort()

                    if text:
                        # Text erkannt - fertig!
                        if attempt > 1:
                            log_print(f"    [RETRY] Text erkannt nach {attempt} Versuchen")
                        break
                    else:
                        # Kein Text - Retry wenn noch Versuche übrig
                        if attempt < 5:
                            if raw_ocr:
                                log_print(f"    [RETRY] Versuch {attempt}/5: Kein DB-Match für OCR-Text: '{raw_ocr}'")
                            else:
                                log_print(f"    [RETRY] Versuch {attempt}/5: Kein Text erkannt, versuche erneut...")
                        else:
                            if raw_ocr:
                                log_print(f"    [SCAN FAILED] OCR erkannte: '{raw_ocr}' - KEINE Übereinstimmung in Datenbank!")
                            else:
                                log_print(f"    [RETRY] Alle 5 Versuche fehlgeschlagen - Kachel leer")

                pyautogui.moveTo(100, 100, duration=0)

                if text:
                    self.detected_items[text] += 1
                    count = self.detected_items[text]
                    log_print(f"  → {text} (#{count})")
                    found_items.append(text)
                    row_items.append(text)

            # Log wenn Reihe nur 1-3 Items hat (normal beim Reverse-Scan)
            if 1 <= len(row_items) <= 3:
                log_print(f"  [INFO] Reihe {row_idx} hat nur {len(row_items)}/4 Items (normal am Ende)")

        return found_items

    def precise_scroll_up_once(self):
        """
        Scrollt einmal nach OBEN (negatives Scrollen).
        Gibt "TOP" zurück wenn Scrollbalken ganz oben ist.
        """
        self.check_abort()

        log_print("  Suche nach Scrollbalken für Upscroll...")

        # Screenshot der Scroll-Region
        scroll_shot = pyautogui.screenshot(region=(
            config.SCROLL_AREA_LEFT,
            config.SCROLL_AREA_TOP,
            config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT,
            config.SCROLL_AREA_BOTTOM - config.SCROLL_AREA_TOP
        ))

        import numpy as np
        img_array = np.array(scroll_shot)

        tolerance = config.SCROLL_COLOR_TOLERANCE
        color1 = np.array(config.SCROLLBAR_COLOR)
        color2 = np.array(config.SCROLLBAR_COLOR_HOVER)

        color_diff1 = np.abs(img_array - color1)
        matches1 = np.all(color_diff1 <= tolerance, axis=2)

        color_diff2 = np.abs(img_array - color2)
        matches2 = np.all(color_diff2 <= tolerance, axis=2)

        matches = matches1 | matches2

        mid_x = (config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT) // 2
        matching_ys = np.where(matches[:, mid_x])[0]

        found_y = -1
        found_y_top = -1

        if len(matching_ys) > 0:
            groups = []
            current_group = [matching_ys[0]]

            for i in range(1, len(matching_ys)):
                if matching_ys[i] - matching_ys[i-1] <= 2:
                    current_group.append(matching_ys[i])
                else:
                    groups.append(current_group)
                    current_group = [matching_ys[i]]
            groups.append(current_group)

            largest_group = max(groups, key=len)
            if len(largest_group) >= 10:
                found_y = int(np.mean(largest_group))
                found_y_top = int(np.min(largest_group))  # Oberes Ende

                absolute_y_top = found_y_top + config.SCROLL_AREA_TOP

                log_print(f"  Scrollbalken gefunden: Oben Y={absolute_y_top}")

                # Prüfe ob oberes Ende am Anfang ist (Y: 220-226)
                log_print(f"  [SCROLLBAR CHECK] Oberes Ende Y={absolute_y_top} (Ziel-Bereich: 220-226)")
                if absolute_y_top >= 220 and absolute_y_top <= 226:
                    log_print(f"  ✓ [SCROLLBAR-TOP] Scrollbalken im Zielbereich erkannt! Y={absolute_y_top}")
                    return "TOP"
                else:
                    log_print(f"  → [SCROLLBAR] Noch nicht im Zielbereich (Differenz: {absolute_y_top - 220}px)")

        # Bestimme Startpunkt
        if found_y == -1:
            cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
            cy = config.SCROLL_AREA_TOP + 50
        else:
            cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
            cy = found_y + config.SCROLL_AREA_TOP

        # Prüfe ob Drag zu weit nach oben gehen würde
        drag_distance = -config.SCROLL_PIXELS_UP  # Negativ = nach oben
        target_y = cy + drag_distance
        min_y = config.SCROLL_AREA_TOP + 10

        if target_y < min_y:
            adjusted_drag = min_y - cy
            log_print(f"  [WARNUNG] Upscroll würde zu weit gehen!")
            log_print(f"    Angepasst: {adjusted_drag}px")
            drag_distance = adjusted_drag

        log_print(f"  Starte Upscroll von Y={cy}, Distanz={drag_distance}px")

        self.check_abort()
        pyautogui.moveTo(cx, cy, duration=0.05)
        time.sleep(0.15)

        self.check_abort()
        pyautogui.drag(0, drag_distance, duration=0.3, button='left')

        wait_steps = 8
        for _ in range(wait_steps):
            self.check_abort()
            time.sleep(config.SCROLL_WAIT / wait_steps)

        self.block_counter += 1
        log_print(f"  Nach oben gescrollt. Block-Zähler: {self.block_counter}")

    def write_results(self):
        """Schreibt finale Ergebnisse im Format: Anzahl, Item-Name"""
        if not self.detected_items:
            return

        try:
            with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # Sortiere Items nach Namen
                for item_name in sorted(self.detected_items.keys()):
                    count = self.detected_items[item_name]
                    f.write(f"{count}, {item_name}\n")

            log_print(f"\n[INFO] {len(self.detected_items)} verschiedene Items in {config.OUTPUT_FILE} gespeichert.")

            # Zeige auch Gesamtzahl aller Items
            total_items = sum(self.detected_items.values())
            log_print(f"[INFO] Insgesamt {total_items} Items gescannt ({len(self.detected_items)} unique).")
        except Exception as e:
            log_print(f"[FEHLER] Konnte Ergebnisse nicht schreiben: {e}")

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

                scan_result = self.scan_8_rows_block()

                # Prüfe ob 2 leere Reihen hintereinander erkannt wurden
                if scan_result == "EMPTY_ROWS":
                    log_print("\n[INFO] 2 leere Reihen hintereinander erkannt → Scrollbalken-Ende-Check...")
                    # Scroll einmal und prüfe ob am Ende
                    scroll_result = self.precise_scroll_down_once()

                    if scroll_result == "END":
                        log_print("[INFO] Scrollbalken-Ende bestätigt! Scan von unten nach oben startet...")
                        self.scan_from_bottom_up()
                        break
                    else:
                        log_print("[INFO] Noch nicht am Ende, Scan wird fortgesetzt.")
                        empty_blocks = 0
                elif scan_result:
                    empty_blocks = 0
                else:
                    empty_blocks += 1
                    log_print(f"  Leerer Block ({empty_blocks}/4)")

                if empty_blocks < 4 and scan_result != "EMPTY_ROWS":
                    scroll_result = self.precise_scroll_down_once()

                    # Prüfe ob Scrollbalken am Ende ist
                    if scroll_result == "END":
                        log_print("\n[INFO] Scrollbalken-Ende erkannt! Scan von unten nach oben startet...")
                        self.scan_from_bottom_up()
                        break

            log_print("\nScan beendet, da 4 leere Blöcke gefunden wurden.")

        except ScanAbortedException:
            # Normal handling für ESC-Abbruch
            pass

        finally:
            # Bei Abbruch: Maus in neutrale Position bewegen
            self.scan_active = False
            pyautogui.moveTo(100, 100, duration=0)  # Instant
            log_print("Maus gestoppt und in Ruheposition bewegt.")

            # Schreibe finale Ergebnisse in detected_items.txt
            self.write_results()