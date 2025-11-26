# -*- coding: utf-8 -*-
"""
ocr_fixes.py - Konfigurationsdatei für OCR-Korrekturen
Hier können häufige OCR-Fehler definiert werden, die automatisch korrigiert werden sollen.
"""

# Dictionary mit OCR-Fehlern und ihren Korrekturen
# Format: "Falsch erkannter Text": "Korrekter Text"
OCR_FIXES = {
    # === Bekannte Probleme ===
    "Olve": "Olive",
    "Helment": "Helmet",
    "Hel met": "Helmet",
    "J-S": "J-5",
    "Morozov SH": "Morozov-SH",
    "CBH-3": "CBH-3",
    "Harizon": "Horizon",  # a ↔ o

    # === Aus Log erkannte Fehler ===
    "@racle Helmet": "Oracle Helmet",
    "Harizon Helmet Rust Society": "Horizon Helmet Rust Society",
    "Paladin Helmet Black/ Silver": "Paladin Helmet Black/Silver",
    "cBH- 3 Helmet Yellow": "CBH-3 Helmet Yellow",
    "cBH-3 Helmet Yellow": "CBH-3 Helmet Yellow",
    'Venture Helmet Rust Society"': "Venture Helmet Rust Society",
    "Morozov-SH-CHelmet Vesper": "Morozov-SH-C Helmet Vesper",
    "AdP-mk4 Core Justified": "ADP-mk4 Core Justified",
    "@RC-mkX Helmet Justified": "ORC-mkX Helmet Justified",
    "orc-mkx Helmet Arctic": "ORC-mkX Helmet Arctic",
    "@RC-mkx Helmet Autumn": "ORC-mkX Helmet Autumn",
    "Argus Helmet Black/White/ Violet": "Argus Helmet Black/White/Violet",
    "Pembroke Helmet RSIIvory Edition": "Pembroke Helmet RSI Ivory Edition",
    "Aztalan Helmet Epoque": "Aztalan Helmet Epoque",  # Falls falsch, hier korrigieren

    # === Zahlen-Buchstaben Verwechslungen ===
    "6-2": "G-2",   # 6 ↔ G
    "0RC": "ORC",   # 0 ↔ O
    "@RC": "ORC",   # @ ↔ O
    "R5I": "RSI",   # 5 ↔ S
    "R51": "RSI",   # 5+1 ↔ S+I
    "1-5": "I-5",   # 1 ↔ I (wenn I gemeint ist)
    "8CS": "BCS",   # 8 ↔ B
    "C-S4": "C-54", # S ↔ 5

    # === Fehlende/falsche Bindestriche ===
    "J5": "J-5",
    "J 5": "J-5",
    "G2": "G-2",
    "G 2": "G-2",

    # === Groß-/Kleinschreibung ===
    "orc-mkx": "ORC-mkX",
    "cbh-3": "CBH-3",
    "adp-mk4": "ADP-mk4",
}

# Zusätzliche Zeichen, die entfernt werden sollen
CHARS_TO_REMOVE = [
    '"',  # Anführungszeichen am Ende
    "'",  # Einfache Anführungszeichen
]

def get_fixes():
    """
    Gibt das OCR-Fixes Dictionary zurück.

    Returns:
        dict: Dictionary mit OCR-Fehlern und Korrekturen
    """
    return OCR_FIXES.copy()

def get_chars_to_remove():
    """
    Gibt die Liste der zu entfernenden Zeichen zurück.

    Returns:
        list: Liste mit Zeichen die entfernt werden sollen
    """
    return CHARS_TO_REMOVE.copy()
