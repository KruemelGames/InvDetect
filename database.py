# -*- coding: utf-8 -*-
"""
database.py – lädt einmalig alle Item-Namen aus deiner inventory.db
Wird von ocr_scanner.py für die Namenskorrektur verwendet
"""

import sqlite3
import os
from config import DB_PATH

# Globale Liste mit allen Item-Namen
ITEM_DATABASE = []

def load_database():
    global ITEM_DATABASE
    if ITEM_DATABASE:  # schon geladen
        return ITEM_DATABASE

    if not os.path.exists(DB_PATH):
        print(f"[DB] Nicht gefunden: {DB_PATH}")
        return []

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Einfach alle Namen holen – GearCrate hat immer eine Spalte "name"
        cur.execute("SELECT name FROM items WHERE name IS NOT NULL AND trim(name) != ''")
        rows = cur.fetchall()
        conn.close()

        ITEM_DATABASE = sorted({row[0].strip() for row in rows})
        print(f"[DB] {len(ITEM_DATABASE)} Items aus inventory.db geladen.")

    except Exception as e:
        print(f"[DB] Fehler beim Laden: {e}")
        ITEM_DATABASE = []

    return ITEM_DATABASE

# Beim ersten Import automatisch laden
load_database()