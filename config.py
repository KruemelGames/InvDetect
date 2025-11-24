# -*- coding: utf-8 -*-
"""
Config – jetzt mit FESTEM OCR-BEREICH (wie du es brauchst)
"""

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# ============= INVENTAR BEREICH =============
INVENTORY_TOP = 220
INVENTORY_BOTTOM = 1021
INVENTORY_LEFT = 1348
INVENTORY_RIGHT = 1790

BORDER_OFFSET_TOP = 4
BORDER_OFFSET_LEFT = 4

TILE_WIDTH = 86
TILE_HEIGHT_SMALL = 86
TILE_HEIGHT_LARGE = 160
TILE_SPACING = 10

# ============= FESTE OCR-REGION (wie du gemessen hast) =============
OCR_LEFT   = 1095
OCR_TOP    = 100
OCR_RIGHT  = 1326
OCR_BOTTOM = 135
OCR_WIDTH  = OCR_RIGHT - OCR_LEFT   # 231 px
OCR_HEIGHT = OCR_BOTTOM - OCR_TOP   # 35 px

MAX_COLUMNS = 4

START_X = INVENTORY_LEFT + BORDER_OFFSET_LEFT
START_Y = INVENTORY_TOP + BORDER_OFFSET_TOP

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
OUTPUT_FILE = "detected_items.txt"

FILTER_PATTERNS = [
    r'Volume:\s*[\d.]+\s*μ?SCU',
    r'Item Type:',
    r'Damage Reduction:',
    r'Temp. Rating:',
    r'Radiation Protection:',
    r'REM/s',
]

SCROLL_AMOUNT = -3
SCROLL_WAIT = 0.4