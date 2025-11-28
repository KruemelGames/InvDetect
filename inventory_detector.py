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
        self.not_detected_items = {}  # Stores OCR text with position: {text: [(page, row, col), ...]}
        self.current_page = 0  # Track current page number
        self.current_row = 0  # Track current row number
        self.current_col = 0  # Track current column number

        # Erstelle Output-Datei beim Start, falls nicht vorhanden
        if not os.path.exists(config.OUTPUT_FILE):
            try:
                with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    f.write("# Inventory Scan Results\n")
                    f.write("# Format: Anzahl, Item-Name\n")
                    f.write("# Waiting for scan to complete...\n")
                log_print(f"[INFO] Output file created: {config.OUTPUT_FILE}")
            except Exception as e:
                log_print(f"[WARNING] Could not create output file: {e}")

    def check_abort(self):
        """Prüft ob ENTF gedrückt wurde und wirft Exception"""
        if keyboard.is_pressed('delete'):
            self.scan_active = False
            import traceback
            # Debug: Zeige wo der Abbruch stattfindet
            stack = traceback.extract_stack()
            caller = stack[-2]  # Die aufrufende Funktion
            log_print(f"\n[ABORT] DELETE pressed at {caller.name}:{caller.lineno}")
            raise ScanAbortedException("DELETE pressed")

    def check_button_brightness(self):
        """
        Prüft die durchschnittliche Graustufenhelligkeit des Buttons im Bereich x1608-1616, y1034-1047.
        Returns:
            bool: True wenn Button aktiv (Helligkeit 65-85), False sonst
        """
        # Screenshot des Button-Bereichs
        button_region = (1608, 1034, 8, 13)  # x, y, width, height
        screenshot = pyautogui.screenshot(region=button_region)

        # Konvertiere zu Graustufen und berechne Durchschnittshelligkeit
        import numpy as np
        from PIL import Image

        # Konvertiere PIL Image zu Graustufen
        gray_image = screenshot.convert('L')

        # Konvertiere zu numpy array für Berechnung
        gray_array = np.array(gray_image)

        # Berechne Durchschnittshelligkeit
        avg_brightness = np.mean(gray_array)

        # Button ist nur aktiv wenn Helligkeit im Bereich 65-85 liegt
        # Zu dunkel (< 65) = kein Button oder inaktiv
        # Zu hell (> 85) = Hintergrund ohne Button
        is_active = 65 <= avg_brightness <= 85

        if is_active:
            status = "Active"
        elif avg_brightness > 85:
            status = "Too bright (background)"
        else:
            status = "Inactive"

        log_print(f"[BUTTON] Brightness: {avg_brightness:.1f} → {status}")

        return is_active

    def reset_to_top(self):
        log_print("Scrolling to top...")

        # Move to first tile (top left)
        first_tile_x = config.START_X + config.HOVER_OFFSET_X
        first_tile_y = config.START_Y + config.FIRST_ROW_Y_OFFSET

        pyautogui.moveTo(first_tile_x, first_tile_y, duration=0)
        time.sleep(0.1)

        # Scroll to top
        for i in range(40):
            self.check_abort()
            pyautogui.scroll(1200)
            time.sleep(0.04)

        for _ in range(15):
            self.check_abort()
            time.sleep(0.1)

        self.block_counter = 0
        log_print("Reset complete")

    def precise_scroll_down_once(self, scroll_distance=None):
        """
        Scrollt nach unten mit angepasster Distanz.

        Args:
            scroll_distance: Pixel zum Scrollen (Standard: config.SCROLL_PIXELS_UP)
        """
        self.check_abort()

        if scroll_distance is None:
            scroll_distance = config.SCROLL_PIXELS_UP

        log_print(f"  Scrollbar detection (distance: {scroll_distance}px)...")

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

                log_print(f"  Scrollbar found: Y={absolute_y}, Bottom={absolute_y_bottom}, Height={scrollbar_height}px")

                # Check if scrollbar is at bottom
                end_min = getattr(config, 'SCROLLBAR_END_MIN', 930)
                end_max = getattr(config, 'SCROLLBAR_END_MAX', 1021)
                if absolute_y_bottom >= end_min and absolute_y_bottom <= end_max:
                    log_print(f"  ✓ [END] Scrollbar at bottom (Y={absolute_y_bottom})")
                    return "END"
            else:
                log_print(f"  [WARNING] Scrollbar too small: {len(largest_group)}px")

        # Determine drag start point
        if found_y == -1:
            log_print("  [WARNING] Scrollbar not found, using fallback")
            cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
            cy = config.SCROLL_AREA_BOTTOM - 50
        else:
            # Erfolgreich: Absolute Koordinaten
            cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
            cy = found_y + config.SCROLL_AREA_TOP

        # 4. Prüfe ob Drag den Scrollbalken aus dem Bereich ziehen würde
        drag_distance = scroll_distance
        target_y = cy + drag_distance
        # Erlaube bis knapp vor SCROLLBAR_END_MAX (damit Scrollbalken im Zielbereich landen kann)
        end_max = getattr(config, 'SCROLLBAR_END_MAX', 1021)
        max_y = end_max + 5  # 5px Puffer über dem Zielbereich

        if target_y > max_y:
            adjusted_drag = max_y - cy
            log_print(f"  [WARNING] Drag too far, adjusting: {drag_distance}px → {adjusted_drag}px")
            drag_distance = adjusted_drag

        log_print(f"  Dragging from X={cx}, Y={cy}, distance={drag_distance}px")

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
        log_print(f"  Scrolled (block {self.block_counter})")


    def scan_rows_block(self, rows_per_block, row_step, tile_height):
        """
        Scannt einen Block mit variabler Reihenzahl (8 für 1x1, 4 für 1x2).

        Args:
            rows_per_block: Anzahl Reihen pro Block (8 oder 4)
            row_step: Abstand zwischen Reihen in px (97 oder 180)
            tile_height: Höhe der Kacheln in px (86 oder 170)

        Returns:
            int: Anzahl leerer Items hintereinander (für Abbruch-Logik), oder -1 wenn Items gefunden
        """
        found = 0
        consecutive_empty_items = 0  # Zähler für leere Items hintereinander

        # 1. Basis-Y berechnen (Startpunkt + Offset für die Mitte der ersten Reihe)
        # Y-Offset = Mitte der Kachel
        first_row_y_offset = tile_height // 2
        base_y = config.START_Y + first_row_y_offset

        # 2. Drift-Kompensation berechnen und anwenden (Maus bewegt sich nach oben)
        drift_val = int(config.DRIFT_COMPENSATION_PER_BLOCK)
        drift_correction = int(self.block_counter * drift_val)
        base_y -= drift_correction

        log_print(f"  Block {self.block_counter + 1}: {rows_per_block} rows, {row_step}px step, drift -{drift_correction}px")

        # 3. Dynamische row_offsets basierend auf Scan-Modus
        row_offsets = [i * row_step for i in range(rows_per_block)]

        for row_idx, offset in enumerate(row_offsets):
            self.check_abort()
            row_y = base_y + offset

            if row_y < 0:
                log_print(f"  [WARNING] Y-coordinate {row_y} < 0! Skipped.")
                continue

            # Calculate absolute row number (1-based)
            self.current_row = (self.block_counter * rows_per_block) + row_idx + 1

            for col in range(config.MAX_COLUMNS):
                self.check_abort()

                # Track current column (1-based)
                self.current_col = col + 1

                # X-Koordinate berechnen
                x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
                y = row_y

                # Adaptive Retry-Logik:
                # - 5 Versuche wenn OCR Text erkennt, aber kein DB-Match
                # - 2 Versuche wenn OCR gar keinen Text erkennt
                text = ""
                raw_ocr = ""
                max_attempts = 2  # Start mit 2 (für "kein Text")

                for attempt in range(1, 6):  # Max. 5 Versuche möglich
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

                    # WICHTIG: Check direkt nach OCR, da OCR lange dauert (100-300ms)
                    self.check_abort()

                    if text:
                        if attempt > 1:
                            log_print(f"    [RETRY] Text found after {attempt} attempts")
                        break
                    elif raw_ocr:
                        if max_attempts < 5:
                            max_attempts = 5
                            log_print(f"    [RETRY] OCR text found but no DB match → max attempts: 5")

                        if attempt < max_attempts:
                            log_print(f"    [RETRY] {attempt}/{max_attempts}: No DB match for '{raw_ocr}'")
                        else:
                            log_print(f"    [FAILED] OCR: '{raw_ocr}' - No DB match after {max_attempts} attempts")
                            # Track unmatched OCR text with position (page, row, column)
                            if raw_ocr not in self.not_detected_items:
                                self.not_detected_items[raw_ocr] = []
                            self.not_detected_items[raw_ocr].append((self.current_page, self.current_row, self.current_col))
                            break
                    else:
                        if attempt < max_attempts:
                            log_print(f"    [RETRY] {attempt}/{max_attempts}: No text")
                        else:
                            log_print(f"    [RETRY] All {max_attempts} attempts failed - empty slot")
                            break

                pyautogui.moveTo(100, 100, duration=0)  # Maus instant aus dem Weg

                if text:
                    self.detected_items[text] += 1  # Zählt jedes Item (auch Duplikate)
                    count = self.detected_items[text]
                    log_print(f"  → {text} (#{count})")
                    found += 1
                    consecutive_empty_items = 0  # Reset bei Fund
                else:
                    consecutive_empty_items += 1
                    log_print(f"  [EMPTY] Checking for next page...")
                    button_active = self.check_button_brightness()

                    if not button_active:
                        log_print(f"  [INACTIVE] No more pages → Ending scan")
                        return 999
                    else:
                        log_print(f"  [ACTIVE] More pages available → Continuing")

        return -1 if found > 0 else consecutive_empty_items

    def scan_last_row(self, tile_height=86):
        """
        Scans only the last row (row 25).

        Args:
            tile_height: Tile height in px (86 or 170)

        Returns:
            int: Number of consecutive empty items, or -1 if items found
        """
        log_print("\n=== SCANNING LAST ROW (25) ===")

        row_y = config.INVENTORY_BOTTOM - config.BORDER_OFFSET_TOP - (tile_height // 2)
        log_print(f"  Scanning at Y={row_y} (tile height: {tile_height}px)")

        found = 0
        consecutive_empty_items = 0

        # Set row number to 25 (last row)
        self.current_row = 25

        for col in range(config.MAX_COLUMNS):
            self.check_abort()

            # Track current column (1-based)
            self.current_col = col + 1

            x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
            y = row_y

            # Adaptive Retry-Logik (wie in scan_8_rows_block)
            text = ""
            raw_ocr = ""
            max_attempts = 2

            for attempt in range(1, 6):
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

                scan_result = ocr_scanner.scan_image_for_text(shot)
                text = scan_result[0].strip()
                raw_ocr = scan_result[1]

                self.check_abort()

                if text:
                    if attempt > 1:
                        log_print(f"    [RETRY] Text found after {attempt} attempts")
                    break
                elif raw_ocr:
                    if max_attempts < 5:
                        max_attempts = 5
                        log_print(f"    [RETRY] OCR text found but no DB match → max attempts: 5")

                    if attempt < max_attempts:
                        log_print(f"    [RETRY] {attempt}/{max_attempts}: No DB match for '{raw_ocr}'")
                    else:
                        log_print(f"    [FAILED] OCR: '{raw_ocr}' - No DB match after {max_attempts} attempts")
                        # Track unmatched OCR text with position (page, row, column)
                        if raw_ocr not in self.not_detected_items:
                            self.not_detected_items[raw_ocr] = []
                        self.not_detected_items[raw_ocr].append((self.current_page, self.current_row, self.current_col))
                        break
                else:
                    if attempt < max_attempts:
                        log_print(f"    [RETRY] {attempt}/{max_attempts}: No text")
                    else:
                        log_print(f"    [RETRY] All {max_attempts} attempts failed - empty slot")
                        break

            pyautogui.moveTo(100, 100, duration=0)

            if text:
                self.detected_items[text] += 1
                count = self.detected_items[text]
                log_print(f"  → {text} (#{count})")
                found += 1
                consecutive_empty_items = 0  # Reset bei Fund
            else:
                consecutive_empty_items += 1
                log_print(f"  [EMPTY] Checking for next page...")
                button_active = self.check_button_brightness()

                if not button_active:
                    log_print(f"  [INACTIVE] No more pages → Ending scan")
                    return 999
                else:
                    log_print(f"  [ACTIVE] More pages available → Continuing")

        return -1 if found > 0 else consecutive_empty_items

    def write_not_detected(self):
        """Writes OCR text that couldn't be matched to database to not_detected.md"""
        if not self.not_detected_items:
            return

        not_detected_file = "not_detected.md"

        try:
            # Read existing items if file exists
            existing_items = {}  # {text: [(page, row, col), ...]}
            if os.path.exists(not_detected_file):
                try:
                    with open(not_detected_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and not line.startswith('---'):
                                # Parse line format: "Item Name - Page X, Row Y, Col Z; Page X, Row Y, Col Z"
                                if ' - ' in line:
                                    parts = line.split(' - ', 1)
                                    item_name = parts[0].strip()
                                    positions_str = parts[1].strip()

                                    positions = []
                                    for pos_str in positions_str.split('; '):
                                        if 'Page' in pos_str and 'Row' in pos_str:
                                            try:
                                                # Extract page, row, and col numbers
                                                pos_parts = pos_str.split(',')
                                                page_part = pos_parts[0].strip()
                                                row_part = pos_parts[1].strip()

                                                page = int(page_part.replace('Page', '').strip())
                                                row = int(row_part.replace('Row', '').strip())

                                                # Check if column exists (new format)
                                                if len(pos_parts) >= 3 and 'Col' in pos_parts[2]:
                                                    col_part = pos_parts[2].strip()
                                                    col = int(col_part.replace('Col', '').strip())
                                                    positions.append((page, row, col))
                                                else:
                                                    # Old format without column
                                                    positions.append((page, row, 0))
                                            except:
                                                pass

                                    if positions:
                                        existing_items[item_name] = positions
                                else:
                                    # Old format without positions
                                    existing_items[line] = []
                except Exception as e:
                    log_print(f"[WARNING] Could not read existing not_detected.md: {e}")

            # Merge with new items
            for item_name, positions in self.not_detected_items.items():
                if item_name in existing_items:
                    # Add new positions, avoiding exact duplicates
                    for pos in positions:
                        if pos not in existing_items[item_name]:
                            existing_items[item_name].append(pos)
                else:
                    existing_items[item_name] = positions

            # Write sorted list
            with open(not_detected_file, 'w', encoding='utf-8') as f:
                f.write("# Items detected by OCR but not matched to database\n")
                f.write("# These items may need to be added to inventory.db\n")
                f.write("# Format: Item Name - Page X, Row Y, Col Z; Page X, Row Y, Col Z\n\n")

                for item_name in sorted(existing_items.keys()):
                    positions = existing_items[item_name]
                    if positions:
                        # Sort positions by page, then row, then col
                        positions.sort()
                        positions_str = '; '.join([f"Page {p}, Row {r}, Col {c}" for p, r, c in positions])
                        f.write(f"{item_name} - {positions_str}\n")
                    else:
                        f.write(f"{item_name}\n")

            new_count = len(self.not_detected_items)
            total_count = len(existing_items)
            log_print(f"[NOT DETECTED] {new_count} new unmatched items ({total_count} total)")
            log_print(f"[NOT DETECTED] Saved to {not_detected_file}")
        except Exception as e:
            log_print(f"[ERROR] Could not write not_detected.md: {e}")

    def write_results(self):
        """Writes final results in format: count, item_name"""
        if not self.detected_items:
            return

        try:
            with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # Sortiere Items nach Namen
                for item_name in sorted(self.detected_items.keys()):
                    count = self.detected_items[item_name]
                    f.write(f"{count}, {item_name}\n")

            total_items = sum(self.detected_items.values())
            log_print(f"\n[RESULTS] {total_items} items scanned ({len(self.detected_items)} unique)")
            log_print(f"[RESULTS] Saved to {config.OUTPUT_FILE}")
        except Exception as e:
            log_print(f"[ERROR] Could not write results: {e}")

        # Write not detected items
        self.write_not_detected()

    def scan_all_tiles(self, scan_mode=1):
        """
        Scannt alle Inventar-Kacheln.

        Args:
            scan_mode: 1 für 1x1 Items (Standard), 2 für 1x2 Items (Undersuits)
        """
        # Parameter basierend auf Modus setzen
        if scan_mode == 2:
            # 1x2 Modus (Undersuits)
            rows_per_block = 4
            row_step = 180  # 170px Item + 10px Abstand
            total_blocks = 6
            tile_height = 170
            # Scroll-Distanz für 4 Reihen (basierend auf Tests)
            # 360px = 9 Reihen → 160px für 4 Reihen
            scroll_pixels = 160
            mode_name = "1x2 (Undersuits)"
        else:
            # 1x1 Modus (Standard)
            rows_per_block = 8
            row_step = 97  # 86px Item + 10px Abstand + 1px
            total_blocks = 3
            tile_height = 86
            scroll_pixels = 322  # Original SCROLL_PIXELS_UP für 8 Reihen
            mode_name = "1x1 (Normal)"

        log_print("\n" + "="*80)
        log_print(f"SCAN STARTED - Mode: {mode_name}")
        log_print(f"Rows/Block: {rows_per_block} | Step: {row_step}px | Blocks: {total_blocks}")
        log_print("="*80 + "\n")

        self.scan_active = True
        scan_iteration = 0  # Zähler für Scan-Durchläufe

        try:
            self.reset_to_top()

            while self.scan_active:
                scan_iteration += 1
                self.current_page = scan_iteration  # Track current page for not_detected
                log_print(f"\n{'='*80}")
                log_print(f"PAGE #{scan_iteration}")
                log_print(f"{'='*80}\n")

                scan_complete = False

                # Reset block_counter at the start of each page
                self.block_counter = 0

                for block_num in range(total_blocks):
                    self.check_abort()

                    log_print(f"\n=== SCANNING BLOCK {self.block_counter + 1} ===")

                    scan_result = self.scan_rows_block(rows_per_block, row_step, tile_height)

                    if scan_result == 999:
                        log_print(f"[END] Button inactive → Scan complete")
                        scan_complete = True
                        break

                    if scan_result == -1:
                        log_print("  Items found")
                    else:
                        log_print(f"  {scan_result} empty slots (button active)")

                    if block_num < (total_blocks - 1):
                        self.check_abort()
                        self.precise_scroll_down_once(scroll_pixels)

                if scan_complete:
                    break

                log_print("\n→ Scrolling to last row...")
                self.check_abort()

                cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
                cy = config.SCROLL_AREA_BOTTOM - 100

                small_scroll = scroll_pixels // rows_per_block
                log_print(f"  Scrolling {small_scroll}px down (1 row)")

                pyautogui.moveTo(cx, cy, duration=0)
                pyautogui.drag(0, small_scroll, duration=0.2, button='left')
                time.sleep(0.3)

                last_row_result = self.scan_last_row(tile_height)
                if last_row_result == 999:
                    log_print(f"[END] Button inactive in row 25 → Scan complete")
                    break

                log_print("\n→ Final button check...")
                self.check_abort()

                button_active = self.check_button_brightness()

                if button_active:
                    log_print("[ACTIVE] Clicking next page button")

                    button_center_x = 1612
                    button_center_y = 1040

                    pyautogui.click(button_center_x, button_center_y)

                    log_print("  Waiting 5s for inventory to load...")
                    for _ in range(50):
                        self.check_abort()
                        time.sleep(0.1)

                    log_print("  Ready for next page\n")

                else:
                    log_print("[INACTIVE] No more pages → Scan complete")
                    break

            log_print("\nScan finished!")

        except ScanAbortedException:
            # Normal handling für ESC-Abbruch
            pass

        finally:
            self.scan_active = False
            pyautogui.moveTo(100, 100, duration=0)
            log_print("Mouse stopped")

            self.write_results()