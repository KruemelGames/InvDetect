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
from ocr_fixes import get_fixes, get_chars_to_remove  # ← OCR-Korrekturen aus externer Datei

# EasyOCR einmalig starten (CPU reicht völlig aus)
# Warnungen unterdrücken
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

reader = easyocr.Reader(['en'], gpu=False, verbose=False)

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

    # Lade OCR-Fixes aus externer Datei
    fixes = get_fixes()
    chars_to_remove = get_chars_to_remove()

    # Entferne unerwünschte Zeichen
    for char in chars_to_remove:
        text = text.replace(char, '')

    # Wende Fixes an
    for wrong, right in fixes.items():
        text = text.replace(wrong, right)

    # Case-insensitive Fuzzy-Matching: Konvertiere zu lowercase für Vergleich
    text_lower = text.lower()
    db_lower = [item.lower() for item in ITEM_DATABASE]

    # Neuer Aufruf ohne limit-Parameter (funktioniert mit 3.x und 4.x)
    result = process.extractOne(text_lower, db_lower, scorer=fuzz.token_sort_ratio)
    if result:
        best_match_lower, score, index = result
        # Threshold von 88 auf 75 gesenkt für bessere Teilwort-Matches
        # z.B. "Oracle Helmet" → "Oracle Helmet Black" (Score ~80)
        if score >= 75:
            # Gebe den ORIGINAL-Namen aus der DB zurück (nicht lowercase)
            return ITEM_DATABASE[index]

    # Kein Match gefunden - gib leeren String zurück
    # Der rohe OCR-Text wird separat für Debug-Ausgabe verwendet
    return ""

def scan_image_for_text(image):
    """
    Hauptfunktion – wird von inventory_detector aufgerufen

    Returns:
        tuple: (korrigierter_text, roher_ocr_text, wurde_korrigiert)
               - korrigierter_text: Der finale Text nach Datenbank-Korrektur (oder "" wenn ungültig)
               - roher_ocr_text: Der ursprüngliche OCR-Text vor Korrektur
               - wurde_korrigiert: True wenn Text durch Datenbank korrigiert wurde
    """
    try:
        processed = preprocess(image)
        results = reader.readtext(processed, detail=0, paragraph=True)
        raw_text = " ".join(results).strip()

        # Volume-Zeile und alles danach abschneiden
        if "Volume:" in raw_text:
            raw_text = raw_text.split("Volume:")[0].strip()

        # Speichere rohen Text für Debug-Ausgabe
        raw_ocr_text = raw_text

        # Datenbank-Korrektur anwenden
        final_text = correct_with_database(raw_text)

        # Prüfe ob Text korrigiert wurde
        wurde_korrigiert = (final_text != raw_text) and final_text in ITEM_DATABASE

        # Nur sinnvolle Ergebnisse zurückgeben
        if len(final_text) >= 4 and not final_text[0].isdigit():
            return (final_text, raw_ocr_text, wurde_korrigiert)
        else:
            # Auch bei ungültigem Ergebnis den rohen Text zurückgeben
            return ("", raw_ocr_text, False)

    except Exception as e:
        print(f"[OCR] Fehler: {e}")
        return ("", "", False)
