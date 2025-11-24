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

class InventoryScanner:
    def __init__(self):
        self.detected_items = set()
        self.block_counter = 0   # wird erst NACH dem Scrollen erhöht → korrekt!

    def reset_to_top(self):
        log_print("Komplett nach oben scrollen...")
        # Maus auf Inventar-Mitte setzen, um Scroll-Events zu empfangen
        cx = (config.INVENTORY_LEFT + config.INVENTORY_RIGHT) // 2
        cy = config.INVENTORY_BOTTOM - 50
        pyautogui.moveTo(cx, cy)
        # 40 Scrolls nach oben, um sicher ganz oben zu sein
        for _ in range(40):
            pyautogui.scroll(1200)
            time.sleep(0.04)
        time.sleep(1.5)
        self.block_counter = 0
        log_print("Zurück am Anfang – Drift-Reset")

    def precise_scroll_down_once(self):
        log_print("  Suche nach Scrollbalken-Farbe und führe Drag-Scroll aus...")

        # 1. Definiere den X-Suchpunkt in der Mitte der Scroll-Spalte (X=1795)
        search_x = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2 
        found_y = -1
        
        # 2. Suche den Y-Startpunkt durch Scannen der Scroll-Spalte nach der Scrollbar-Farbe
        # Scanne von unten nach oben (geht schneller)
        for y in range(config.SCROLL_AREA_BOTTOM - 20, config.SCROLL_AREA_TOP + 20, -10):
            if pyautogui.pixelMatchesColor(search_x, y, config.SCROLLBAR_COLOR, tolerance=config.SCROLL_COLOR_TOLERANCE):
                found_y = y
                log_print(f"  Scrollbalken-Farbe gefunden bei Y={found_y}")
                break
        
        # 3. Bestimme den finalen Drag-Startpunkt
        if found_y == -1:
            log_print("  [WARNUNG] Scrollbalken-Farbe nicht gefunden. Nutze Fallback.")
            cx = search_x
            cy = config.SCROLL_AREA_BOTTOM - 50 
        else:
            # Erfolgreich: Startpunkt 10px über dem gefundenen Pixel (tiefer im Balken)
            cx = search_x
            cy = found_y - 10 
        
        log_print(f"  Starte Drag von X={cx}, Y={cy} für {config.SCROLL_DURATION}s") 
        
        # 4. Maus zum Startpunkt bewegen und ziehen
        pyautogui.moveTo(cx, cy, duration=0.2) 
        
        # **FINALE KORREKTUR:** Positiver Wert = Bewegung nach UNTEN, was das Inventar nach UNTEN scrollt.
        pyautogui.dragRel(
            0, 
            config.SCROLL_PIXELS_UP, # Positiver Wert (+101) = Bewegung nach unten
            duration=config.SCROLL_DURATION, 
            button='left'
        )
        time.sleep(config.SCROLL_WAIT)

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
        
        log_print(f"  Block {self.block_counter + 1} → Y-Korrektur: -{drift_correction}px → erste Reihe bei y={base_y}")

        # 3. Dynamische row_offsets verwenden (FIX für 97px Zeilenabstand)
        try:
            row_offsets = [i * config.ROW_STEP for i in range(8)]
        except AttributeError:
            log_print("FEHLER: config.ROW_STEP nicht gefunden! Nutze Fallback 97px.")
            row_offsets = [i * 97 for i in range(8)]


        for offset in row_offsets:
            row_y = base_y + offset
            
            # Sicherheitscheck: verhindert Abstürze durch negative Y-Koordinaten
            if row_y < 0:
                log_print(f"  [ACHTUNG] Y-Koordinate {row_y} ist < 0! Scan übersprungen.")
                continue

            for col in range(config.MAX_COLUMNS):
                # X-Koordinate berechnen
                x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
                y = row_y

                pyautogui.moveTo(x, y, duration=0.05)
                time.sleep(0.28) # Warten auf Tooltip-Anzeige

                # Screenshot des OCR-Bereichs
                shot = pyautogui.screenshot(region=(
                    config.OCR_LEFT, config.OCR_TOP,
                    config.OCR_WIDTH, config.OCR_HEIGHT
                ))

                text = ocr_scanner.scan_image_for_text(shot).strip()
                pyautogui.moveTo(100, 100)  # Maus aus dem Weg

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
        self.reset_to_top()

        empty_blocks = 0

        while empty_blocks < 4:
            log_print(f"\n=== BLOCK {self.block_counter + 1} WIRD GESCANNT ===")
            
            if self.scan_8_rows_block():
                empty_blocks = 0
            else:
                empty_blocks += 1
                log_print(f"  Leerer Block ({empty_blocks}/4)")

            if empty_blocks < 4:
                self.precise_scroll_down_once()

        log_print("\nScan beendet, da 4 leere Blöcke gefunden wurden.")