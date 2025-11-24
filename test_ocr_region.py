# -*- coding: utf-8 -*-
"""
Testet exakt den OCR-Bereich, den du angegeben hast
Speichert ein Bild: ocr_region_test.png
"""

import pyautogui
import time
from PIL import Image

# Deine Koordinaten aus config.py
OCR_LEFT   = 1095
OCR_TOP    = 100
OCR_RIGHT  = 1326
OCR_WIDTH  = OCR_RIGHT - OCR_LEFT   # 231
OCR_HEIGHT = 135 - 100              # 35

print("In 3 Sekunden wird der OCR-Bereich als Bild gespeichert...")
print(f"Bereich: X={OCR_LEFT}-{OCR_RIGHT}, Y={OCR_TOP}-{135} → {OCR_WIDTH}x{OCR_HEIGHT}px")
time.sleep(3)

# Screenshot machen
screenshot = pyautogui.screenshot(region=(OCR_LEFT, OCR_TOP, OCR_WIDTH, OCR_HEIGHT))

# Als Bild speichern
screenshot.save("ocr_region_test.png")
print("Fertig! Schau dir jetzt die Datei an: ocr_region_test.png")

# Optional: direkt öffnen (Windows)
import os
os.startfile("ocr_region_test.png")