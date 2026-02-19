# Screen Text Analyzer

Continuously reads text visible on your screen using OCR, then prints live analysis in the terminal.

## Install

1. Install Python deps:
   ```bash
   pip install -r requirements.txt
   ```
2. Install Tesseract OCR binary:
   - macOS (Homebrew):
     ```bash
     brew install tesseract
     ```

## macOS permissions

Grant your terminal app Screen Recording permission:
- System Settings -> Privacy & Security -> Screen Recording

Then restart terminal/Codex app.

## Run

```bash
python3 screen_text_analyzer.py
```

Useful options:
- `--interval 1.5` capture every 1.5s
- `--region 0,0,1440,900` analyze a specific rectangle
- `--history 12` keep more recent captures in rolling topic analysis

Example:
```bash
python3 screen_text_analyzer.py --interval 2 --region 100,80,1300,900
```
