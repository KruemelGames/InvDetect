# -*- coding: utf-8 -*-
"""
OCR Scanner für InvDetect
Liest Text aus Screenshots mit Tesseract
"""

import pytesseract
from PIL import Image
import re
import config

# Tesseract Pfad setzen
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH


def scan_image_for_text(image):
    """
    Scannt ein Bild und gibt den erkannten Text zurück
    
    Args:
        image: PIL Image Objekt
        
    Returns:
        str: Erkannter Text (gefiltert)
    """
    try:
        # OCR durchführen
        text = pytesseract.image_to_string(image, lang='eng')
        
        # Text bereinigen
        text = text.strip()
        
        # Filter anwenden
        filtered_text = filter_text(text)
        
        return filtered_text
        
    except Exception as e:
        print(f"❌ OCR Fehler: {e}")
        return ""


def filter_text(text):
    """
    Filtert unerwünschte Textteile raus
    
    Args:
        text: Original Text
        
    Returns:
        str: Gefilterter Text
    """
    if not text:
        return ""
    
    # Alle Zeilen durchgehen
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Prüfen ob Zeile gefiltert werden soll
        should_filter = False
        for pattern in config.FILTER_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                should_filter = True
                break
        
        # Nur behalten wenn nicht gefiltert
        if not should_filter:
            filtered_lines.append(line)
    
    # Zusammenfügen
    result = '\n'.join(filtered_lines)
    return result.strip()


def preprocess_image(image):
    """
    Bereitet Bild für bessere OCR vor
    
    Args:
        image: PIL Image Objekt
        
    Returns:
        PIL Image: Bearbeitetes Bild
    """
    # Kontrast erhöhen für bessere OCR
    from PIL import ImageEnhance
    
    # Zu Graustufen
    image = image.convert('L')
    
    # Kontrast erhöhen
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Helligkeit anpassen
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.2)
    
    return image
