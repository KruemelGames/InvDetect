# -*- coding: utf-8 -*-
"""
config.py – Final korrigierte Geometrie und Scroll-Parameter für Star Citizen Inventar-Scan
"""

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Inventar-Rahmen (Universal Inventory bei 1920×1080)
INVENTORY_TOP = 220
INVENTORY_BOTTOM = 1021
INVENTORY_LEFT = 1348
INVENTORY_RIGHT = 1790

# Scrollbalken-Ende-Erkennung (unteres Ende des Scrollbalkens)
SCROLLBAR_END_MIN = 1010  # Untere Grenze für "am Ende" (vorher 930 - zu niedrig!)
SCROLLBAR_END_MAX = 1021  # Obere Grenze (INVENTORY_BOTTOM)

BORDER_OFFSET_TOP = 4
BORDER_OFFSET_LEFT = 4

TILE_WIDTH = 86
TILE_HEIGHT = 86         # Kachelhöhe (zur Klarheit hinzugefügt)
TILE_SPACING = 10

# NEU: Exakte Schrittweite zur nächsten Reihe
ROW_STEP = 97            # 86px Kachel + 10px Abstand + 1px Korrektur = 97px

# --- SCROLL-PARAMETER (FÜR PIXELGENAUES DRAG-SCROLLEN MIT FARBSUCHE) ---
# Der definierte Bereich, in dem sich der Scrollbalken befindet
SCROLL_AREA_LEFT = 1790 
SCROLL_AREA_TOP = 220
SCROLL_AREA_RIGHT = 1800
SCROLL_AREA_BOTTOM = 1022

# Die Farben des Scrollbalken-Daumens
SCROLLBAR_COLOR = (0, 131, 158)  # RGB für #00839e (nicht gehovert)
SCROLLBAR_COLOR_HOVER = (0, 193, 178)  # RGB für #00c1b2 (gehovert)
SCROLL_COLOR_TOLERANCE = 15     # Toleranz für Farbunterschiede (Wichtig für Zuverlässigkeit)

# Fester OCR-Bereich (Tooltip oben mittig)
OCR_LEFT   = 1095
OCR_TOP    = 100
OCR_RIGHT  = 1326
OCR_BOTTOM = 135
OCR_WIDTH  = OCR_RIGHT - OCR_LEFT
OCR_HEIGHT = OCR_BOTTOM - OCR_TOP

MAX_COLUMNS = 4

START_X = INVENTORY_LEFT + BORDER_OFFSET_LEFT    # 1352
START_Y = INVENTORY_TOP + BORDER_OFFSET_TOP      # 224

# Exaktes 101px Drag-Scroll
SCROLL_PIXELS_UP = 322
SCROLL_DURATION = 0.5  # Drag-Dauer (verwendet in pyautogui.drag)
SCROLL_WAIT = 0.6      # Wartezeit nach Scroll (für Spiel-Latenz)

# DATEIEN
OUTPUT_FILE = "detected_items.txt"
LOG_FILE    = "scan_log.txt"

# DEINE DATENBANK
DB_PATH = r"C:\Users\kruem\PycharmProjects\GearCrate\data\inventory.db"

# ←←← HIER SIND DIE KERN-KORREKTUREN ←←←
HOVER_OFFSET_X = 53                     # X-Position innerhalb des Tiles
FIRST_ROW_Y_OFFSET = 38                 # Y-Offset zur Mitte der ersten Reihe
DRIFT_COMPENSATION_PER_BLOCK = 0      # 28px-4px = 24px Korrektur pro Scroll (zu viel gescrollt)