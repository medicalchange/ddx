# Differential Diagnosis Cards

Static browser app for storing and editing symptom-based differential diagnosis cards.

## Project scope

This repository contains the DDX website only:

- `index.html`
- `style.css`
- `app.js`
- `data/seed-data.json`

The app is fully client-side and can be hosted on any static host.

## Features

- Pre-seeded symptom list from the University of Toronto Diagnostic Checklist
- Searchable symptom cards
- Editable fields for:
  - common causes
  - can't-miss causes
  - red flags
  - initial workup
  - references
  - notes
  - last reviewed date
- Local browser storage with JSON export/import

## Local development

Open `index.html` directly in a browser, or serve the folder with a simple static server such as:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Seed data scripts

The `scripts/` folder contains lightweight helpers for maintaining `data/seed-data.json`:

- `scripts/update_seed.py` fetches and rebuilds seed data from the University of Toronto source XML.
- `scripts/export_seed_json.py` starts a tiny local endpoint for saving seed JSON during manual data work.

## Notes

- Educational organizer only; not clinical decision support.
- Data stays in browser storage unless exported by the user.
