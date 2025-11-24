# -*- coding: utf-8 -*-
"""
Konfiguration für InvDetect - Star Citizen Inventar Scanner
Alle Koordinaten und Einstellungen
"""

# ============ BILDSCHIRM ============
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# ============ INVENTAR BEREICH ============
# Inventar Rahmen Positionen (hochkant x vertikal)
INVENTORY_TOP = 220      # Oberkante Inventar
INVENTORY_BOTTOM = 1021  # Unterkante Inventar
INVENTORY_LEFT = 1348    # Linke Kante Inventar
INVENTORY_RIGHT = 1790   # Rechte Kante Inventar

# Abstand vom Rahmen zur ersten Kachel
BORDER_OFFSET_TOP = 4    # 4px von oben
BORDER_OFFSET_LEFT = 4   # 4px von links

# ============ KACHEL GRÖßEN ============
# Alle Kacheln sind HOCHKANT (Breite x Höhe)
TILE_WIDTH = 86          # Breite jeder Kachel
TILE_HEIGHT_SMALL = 86   # 1x1 Kachel Höhe
TILE_HEIGHT_LARGE = 160  # 1x2 Kachel Höhe

# Abstand zwischen Kacheln
TILE_SPACING = 10        # 10px zwischen Kacheln

# ============ RASTER LAYOUT ============
MAX_COLUMNS = 4          # 4 Kacheln nebeneinander

# ============ START POSITION ============
# Erste Kachel Position (oben links)
START_X = INVENTORY_LEFT + BORDER_OFFSET_LEFT
START_Y = INVENTORY_TOP + BORDER_OFFSET_TOP

# ============ TESSERACT ============
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ============ HOTKEY ============
TRIGGER_KEY = 'insert'   # "Einfügen" Taste

# ============ OUTPUT ============
OUTPUT_FILE = "detected_items.txt"

# ============ OCR FILTER ============
# Diese Texte werden herausgefiltert
FILTER_PATTERNS = [
    r'Volume:\s*[\d.]+\s*μSCU',  # Filtert "Volume: 23000 μSCU"
    r'Volume:\s*[\d.]+\s*uSCU',  # Filtert auch "uSCU" ohne μ
]

# ============ SCROLL EINSTELLUNGEN ============
SCROLL_AMOUNT = -3       # Negativ = nach unten scrollen
SCROLL_WAIT = 0.3        # Wartezeit nach Scroll (Sekunden)
