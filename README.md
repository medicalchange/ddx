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

## Run on Mac

1. Open Terminal.
2. Go to the project folder:
   ```bash
   cd "/Users/aaharris/Desktop/CODEX/what can you do"
   ```
3. Start a local server:
   ```bash
   python3 -m http.server 8000
   ```
4. Open in browser:
   [http://localhost:8000](http://localhost:8000)

## Notes

- This is an educational organizer, not clinical decision support.
- The first visit asks you to set a password before you can edit cards; unlock the overlay to continue anytime.
- Use the `Change password` button (top right) once you are unlocked to update your password later.
- Data stays in your browser unless you export it.
