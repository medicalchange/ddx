# Differential Diagnosis Cards (Browser App)

A beginner-friendly local web app for storing symptom-based differential diagnosis cards.

## Features

- Pre-seeded symptom list from the University of Toronto Diagnostic Checklist mobile page
- Seed data includes ready-to-use common and can't-miss causes (see `data/seed-data.json`)
- Search by symptom
- Edit each card with:
  - Common causes
  - Can't-miss causes
  - Red flags
  - Initial workup
  - References
  - Notes
  - Last reviewed date
- Local-only storage in browser `localStorage`
- Export/import your data as JSON

## Hosting

- The app is a static HTML/CSS/JS bundle and can be served from any static host (GitHub Pages, static file server, etc.).

## Notes

- This is an educational organizer, not clinical decision support.
- Data stays in your browser unless you export it.

## Live Screen Text Monitor (Python)

This repo now includes a separate script that can continuously OCR the text on your screen and analyze updates.

### Files

- `scripts/screen_text_monitor.py`
- `scripts/requirements-screen-monitor.txt`

### Setup (macOS)

1. Install tesseract OCR binary:
   - `brew install tesseract`
2. Install Python dependencies:
   - `python3 -m pip install -r scripts/requirements-screen-monitor.txt`
3. Grant Screen Recording permission to your terminal app in System Settings.

### Run

- Local analysis mode:
  - `python3 scripts/screen_text_monitor.py --interval 2 --min-change-chars 50 --show-raw-text`
- OpenAI analysis mode:
  - `export OPENAI_API_KEY=...`
  - `python3 scripts/screen_text_monitor.py --model gpt-4.1-mini --interval 2`

### Notes

- The script captures the primary display repeatedly, extracts text with OCR, then only re-analyzes when text changes enough.
- OCR quality depends on font size, contrast, and UI scaling.
