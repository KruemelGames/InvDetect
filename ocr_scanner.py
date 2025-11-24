# -*- coding: utf-8 -*-
"""
OCR Scanner – EasyOCR Edition
Perfekt für Star Citizen Helm-Tooltips (2 Zeilen)
"""

import easyocr
import cv2
import numpy as np
from PIL import Image

# EasyOCR einmal starten – Englisch, CPU reicht völlig
reader = easyocr.Reader(['en'], gpu=False)   # gpu=True falls du NVIDIA hast

def preprocess_for_easyocr(img):
    """Optimiert für deine 231×35px Region"""
    # Graustufen
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    
    # 6-fach hochskalieren (winzige Schrift → groß)
    gray = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
    
    # Kontrast extrem boosten
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # Scharfzeichnen
    kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
    gray = cv2.filter2D(gray, -1, kernel)
    
    return gray

def scan_image_for_text(image):
    try:
        # Pre-Processing
        processed = preprocess_for_easyocr(image)
        
        # EasyOCR loslassen
        results = reader.readtext(processed, detail=0, paragraph=True)
        
        # Alles zusammen und nur die erste sinnvolle Zeile nehmen (der Helm-Name)
        text = " ".join(results).strip()
        
        # Alles nach "Volume:" abschneiden → nur Name bleibt
        if "Volume:" in text:
            text = text.split("Volume:")[0].strip()
            
        # Zusätzlichen Müll rausfiltern
        trash = ["Item Type:", "Damage Reduction:", "Temp. Rating:", "Radiation", "REM/s"]
        for t in trash:
            if t in text:
                text = text.split(t)[0].strip()
                
        # Mindestens 5 Zeichen und keine Zahlen am Anfang
        if len(text) < 5 or text[0].isdigit():
            return ""
            
        return text
        
    except Exception as e:
        print("EasyOCR Fehler:", e)
        return ""