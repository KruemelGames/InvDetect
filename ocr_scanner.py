# -*- coding: utf-8 -*-
"""
ocr_scanner.py – finale Version
EasyOCR + automatische Namenskorrektur über deine inventory.db
"""

import easyocr
import cv2
import numpy as np
from rapidfuzz import fuzz, process
from database import ITEM_DATABASE   # ← alle Namen aus deiner DB

# EasyOCR einmalig starten (CPU reicht völlig aus)
reader = easyocr.Reader(['en'], gpu=False)

def preprocess(img):
    """Optimiert für deine 231×35px Tooltip-Region"""
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
    gray = cv2.filter2D(gray, -1, kernel)
    return gray

def correct_with_database(text):
    """Korrigiert OCR-Fehler – kompatibel mit allen rapidfuzz-Versionen"""
    if not text or len(text) < 4 or not ITEM_DATABASE:
        return text.strip()

    # Hartkodierte Fixes
    fixes = {
        "Olve": "Olive",
        "Helment": "Helmet",
        "Hel met": "Helmet",
        "J-S": "J-5",
        "Morozov SH": "Morozov-SH",
        "CBH-3": "CBH-3",
    }
    for wrong, right in fixes.items():
        text = text.replace(wrong, right)

    # Neuer Aufruf ohne limit-Parameter (funktioniert mit 3.x und 4.x)
    result = process.extractOne(text, ITEM_DATABASE, scorer=fuzz.token_sort_ratio)
    if result:
        best_match, score, _ = result
        if score >= 88:
            return best_match

    return text.strip()

def scan_image_for_text(image):
    """Hauptfunktion – wird von inventory_detector aufgerufen"""
    try:
        processed = preprocess(image)
        results = reader.readtext(processed, detail=0, paragraph=True)
        raw_text = " ".join(results).strip()

        # Volume-Zeile und alles danach abschneiden
        if "Volume:" in raw_text:
            raw_text = raw_text.split("Volume:")[0].strip()

        # Datenbank-Korrektur anwenden
        final_text = correct_with_database(raw_text)

        # Nur sinnvolle Ergebnisse zurückgeben
        if len(final_text) >= 4 and not final_text[0].isdigit():
            return final_text
        else:
            return ""

    except Exception as e:
        print(f"[OCR] Fehler: {e}")
        return ""
