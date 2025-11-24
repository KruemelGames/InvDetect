# -*- coding: utf-8 -*-
"""
Inventory Detector für InvDetect
Findet und scannt alle Items im Inventar
"""

import pyautogui
from PIL import Image
import time
import numpy as np
import config
import ocr_scanner

# PyAutoGUI Sicherheit ausschalten (sonst Fehler bei Ecken)
pyautogui.FAILSAFE = False


class InventoryScanner:
    """Scannt das Star Citizen Inventar"""
    
    def __init__(self):
        self.detected_items = []
        self.current_row = 0
        self.current_col = 0
        
    def detect_tile_size(self, x, y):
        """
        Erkennt ob Kachel 1x1 oder 1x2 ist
        
        Args:
            x, y: Position der Kachel
            
        Returns:
            str: 'small' oder 'large'
        """
        # Screenshot der Kachel + etwas drüber/drunter
        check_height = config.TILE_HEIGHT_LARGE + 20
        
        screenshot = pyautogui.screenshot(region=(
            x, y,
            config.TILE_WIDTH,
            check_height
        ))
        
        # Zu Array konvertieren
        img_array = np.array(screenshot)
        
        # Durchschnittliche Helligkeit in verschiedenen Bereichen
        small_area = img_array[0:config.TILE_HEIGHT_SMALL, :, :]
        large_area = img_array[config.TILE_HEIGHT_SMALL:config.TILE_HEIGHT_LARGE, :, :]
        
        # Helligkeit berechnen
        small_brightness = np.mean(small_area)
        large_brightness = np.mean(large_area)
        
        # Wenn unterer Bereich deutlich dunkler = nur 1x1
        # Wenn ähnlich hell = 1x2 Kachel
        brightness_diff = abs(small_brightness - large_brightness)
        
        if brightness_diff > 30:  # Schwellwert für Unterschied
            return 'small'
        else:
            return 'large'
    
    def get_tile_position(self, row, col):
        """
        Berechnet Position einer Kachel
        
        Args:
            row: Reihe (0-basiert)
            col: Spalte (0-basiert)
            
        Returns:
            tuple: (x, y) Position
        """
        x = config.START_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
        y = config.START_Y + row * (config.TILE_HEIGHT_SMALL + config.TILE_SPACING)
        
        return (x, y)
    
    def capture_tile(self, x, y, tile_size):
        """
        Macht Screenshot von einer Kachel
        
        Args:
            x, y: Position
            tile_size: 'small' oder 'large'
            
        Returns:
            PIL Image: Screenshot
        """
        if tile_size == 'small':
            height = config.TILE_HEIGHT_SMALL
        else:
            height = config.TILE_HEIGHT_LARGE
        
        screenshot = pyautogui.screenshot(region=(
            x, y,
            config.TILE_WIDTH,
            height
        ))
        
        return screenshot
    
    def scan_tile(self, x, y):
        """
        Scannt eine einzelne Kachel
        
        Args:
            x, y: Position der Kachel
            
        Returns:
            str: Erkannter Text oder None
        """
        # Maus zur Kachel bewegen (für Mouse-Over Effekt)
        pyautogui.moveTo(x + config.TILE_WIDTH // 2, 
                        y + config.TILE_HEIGHT_SMALL // 2,
                        duration=0.1)
        time.sleep(0.2)  # Warten auf Tooltip
        
        # Kachelgröße erkennen
        tile_size = self.detect_tile_size(x, y)
        
        print(f"  📦 Kachel bei ({x}, {y}) - Größe: {tile_size}")
        
        # Screenshot machen
        screenshot = self.capture_tile(x, y, tile_size)
        
        # Bild vorverarbeiten
        processed = ocr_scanner.preprocess_image(screenshot)
        
        # OCR durchführen
        text = ocr_scanner.scan_image_for_text(processed)
        
        if text:
            print(f"  ✅ Gefunden: {text}")
            return text
        else:
            print(f"  ⚠️ Kein Text erkannt")
            return None
    
    def scroll_inventory(self):
        """Scrollt das Inventar nach unten"""
        print("  📜 Scrolle nach unten...")
        
        # Maus ins Inventar bewegen
        center_x = (config.INVENTORY_LEFT + config.INVENTORY_RIGHT) // 2
        center_y = (config.INVENTORY_TOP + config.INVENTORY_BOTTOM) // 2
        
        pyautogui.moveTo(center_x, center_y)
        time.sleep(0.1)
        
        # Scrollen
        pyautogui.scroll(config.SCROLL_AMOUNT)
        time.sleep(config.SCROLL_WAIT)
    
    def scan_all_tiles(self):
        """
        Scannt alle Kacheln im Inventar
        
        Returns:
            list: Alle gefundenen Items
        """
        print("\n🚀 Starte Inventar-Scan...\n")
        
        self.detected_items = []
        row = 0
        col = 0
        empty_rows = 0
        
        while True:
            # Zeile scannen
            row_items = []
            
            for col in range(config.MAX_COLUMNS):
                x, y = self.get_tile_position(row, col)
                
                # Prüfen ob noch im Inventar
                if y > config.INVENTORY_BOTTOM - config.TILE_HEIGHT_SMALL:
                    print(f"⚠️ Zeile {row} außerhalb Inventar - scrolle...")
                    self.scroll_inventory()
                    # Position neu berechnen
                    x, y = self.get_tile_position(row, col)
                
                # Kachel scannen
                item_text = self.scan_tile(x, y)
                
                if item_text:
                    row_items.append(item_text)
                    self.detected_items.append(item_text)
            
            # Wenn Zeile leer = Ende erreicht
            if not row_items:
                empty_rows += 1
                if empty_rows >= 2:  # 2 leere Zeilen = sicher fertig
                    print("\n✅ Scan abgeschlossen - keine weiteren Items\n")
                    break
            else:
                empty_rows = 0
            
            # Nächste Zeile
            row += 1
            
            # Sicherheit: Maximal 50 Zeilen
            if row > 50:
                print("\n⚠️ Maximum erreicht (50 Zeilen)")
                break
        
        return self.detected_items
    
    def save_to_file(self, filename=None):
        """
        Speichert Items in Textdatei
        
        Args:
            filename: Dateiname (optional)
        """
        if filename is None:
            filename = config.OUTPUT_FILE
        
        if not self.detected_items:
            print("⚠️ Keine Items zum Speichern!")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for item in self.detected_items:
                    f.write(item + '\n')
            
            print(f"\n💾 {len(self.detected_items)} Items gespeichert in: {filename}")
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
