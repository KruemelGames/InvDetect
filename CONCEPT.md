# InvDetect - Proof of Concept

## What It Does

InvDetect automatically scans your Star Citizen inventory by:
1. Hovering over each inventory slot
2. Reading the tooltip with (Optical Character Recognition) OCR (EasyOCR)
3. Matching items against a database (fuzzy matching)
4. Detecting when to move to the next page

## How It Works

### 1. Grid Navigation
- Scans a 5-column × 25-row inventory grid
- Supports two modes:
  - **1x1 mode**: Standard items (86×86px)
  - **1x2 mode**: Undersuits (86×170px)

### 2. Smart Scrolling
- Uses pixel-perfect scrollbar detection
- Automatically scrolls through inventory blocks
- Adapts scroll distance based on item size

### 3. Multi-Page Detection
- Checks button brightness (65-85 range = active)
- Automatically clicks "next page" button
- Stops when no more pages available

### 4. Empty Item Detection
- Checks button status on **every empty slot**
- Stops immediately if button inactive
- Saves time by not scanning empty sections

### 5. OCR with Error Correction
- External fix file (`ocr_fixes.py`) for common OCR mistakes
- Case-insensitive fuzzy matching (75% threshold)
- Adaptive retry logic:
  - 2 attempts if no OCR text
  - 5 attempts if OCR text found but no DB match

## Key Features

✅ **Multi-page support** - Scans across all inventory pages
✅ **Two scan modes** - Handles different item sizes
✅ **Smart detection** - Stops scanning when inventory ends
✅ **Error correction** - Fixes common OCR mistakes automatically
✅ **Abort anytime** - Press DELETE to stop scanning

## Output

Results saved to `detected_items.txt`:
```
3, Pembroke Helmet RSI Ivory Edition
2, Oracle Helmet Black
1, Aztalan Helmet Epoque
```

Format: `quantity, item_name`

## Technical Stack

- **Python 3.x**
- **EasyOCR** - Text recognition
- **PyAutoGUI** - Mouse control & screenshots
- **RapidFuzz** - Fuzzy string matching
- **SQLite** - Item database (GearCrate inventory.db)

## Performance

- ~1.38 seconds per item slot
- ~5 minutes for 300 items
- Adaptive retry reduces wasted time on empty slots
