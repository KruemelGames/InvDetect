# -*- coding: utf-8 -*-
"""
Inventory Detector – FINAL mit EasyOCR + fester OCR-Region
"""

import pyautogui
import time
import config
import ocr_scanner
import keyboard

# Logging wie immer
def log_print(*args, **kwargs):
    msg = " ".join(map(str, args))
    print(msg, **kwargs)
    try:
        with open("scan_log.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass

pyautogui.FAILSAFE = False


class InventoryScanner:
    def __init__(self):
        self.detected_items = []

    def check_escape(self):
        if keyboard.is_pressed('esc'):
            log_print("\nESC GEDRÜCKT → Scan sofort abgebrochen!")
            raise KeyboardInterrupt

    def get_tile_position(self, row, col):
        x = config.START_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
        y = config.START_Y + row * (config.TILE_HEIGHT_SMALL + config.TILE_SPACING)
        return x, y

    def scan_tile(self, x, y):
        self.check_escape()

        # Maus in die Mitte der Kachel → Tooltip erscheint
        pyautogui.moveTo(x + config.TILE_WIDTH // 2, y + 30, duration=0.1)
        time.sleep(0.35)   # stabiler Tooltip

        log_print(f"  Scanne Kachel ({x}, {y})")

        # FESTER OCR-BEREICH (wie du gemessen hast)
        screenshot = pyautogui.screenshot(region=(
            config.OCR_LEFT,
            config.OCR_TOP,
            config.OCR_WIDTH,
            config.OCR_HEIGHT
        ))

        # EasyOCR macht das Pre-Processing selbst → kein preprocess_image_helmet mehr nötig
        text = ocr_scanner.scan_image_for_text(screenshot).strip()

        # Maus weg
        pyautogui.moveTo(100, 100)

        if text:
            log_print(f"  GEFUNDEN → {text}")
            self.detected_items.append(text)
            self.save_to_file(text)
            return text
        else:
            log_print(f"  leer / Müll")
            return None

    def scroll_inventory(self):
        self.check_escape()
        log_print("  Scrolle nach unten...")
        cx = (config.INVENTORY_LEFT + config.INVENTORY_RIGHT) // 2
        cy = (config.INVENTORY_TOP + config.INVENTORY_BOTTOM) // 2
        pyautogui.moveTo(cx, cy)
        time.sleep(0.1)
        pyautogui.scroll(config.SCROLL_AMOUNT)
        time.sleep(config.SCROLL_WAIT)

    def save_to_file(self, item):
        try:
            with open(config.OUTPUT_FILE, 'a', encoding='utf-8') as f:
                f.write(item + '\n')
        except Exception as e:
            log_print(f"Save-Fehler: {e}")

    def scan_all_tiles(self):
        log_print("\nScan läuft – ESC = sofort stoppen!\n")
        row = 0
        empty_rows = 0

        while row < 50:
            self.check_escape()
            row_has_item = False

            for col in range(config.MAX_COLUMNS):
                x, y = self.get_tile_position(row, col)
                if self.scan_tile(x, y):
                    row_has_item = True

            if not row_has_item:
                empty_rows += 1
                if empty_rows >= 2:
                    log_print("\nKeine Items mehr → Scan fertig!")
                    break
            else:
                empty_rows = 0

            row += 1
            if row < 49:
                self.scroll_inventory()
            time.sleep(0.12)

        log_print("\nScan beendet.")