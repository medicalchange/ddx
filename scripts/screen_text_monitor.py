#!/usr/bin/env python3
"""Continuously OCR on-screen text and analyze changes.

macOS usage notes:
- Requires Screen Recording permission for Terminal/iTerm.
- Requires tesseract OCR binary installed (e.g. `brew install tesseract`).
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

try:
    import mss
except ImportError as exc:  # pragma: no cover - startup dependency check
    raise SystemExit("Missing dependency: mss. Run: pip install -r scripts/requirements-screen-monitor.txt") from exc

try:
    import pytesseract
except ImportError as exc:  # pragma: no cover - startup dependency check
    raise SystemExit("Missing dependency: pytesseract. Run: pip install -r scripts/requirements-screen-monitor.txt") from exc

from PIL import Image


@dataclass
class AnalysisConfig:
    interval: float
    min_change_chars: int
    show_raw_text: bool
    model: str


def normalize_text(text: str) -> str:
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def capture_ocr_text() -> str:
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # full primary display
        shot = sct.grab(monitor)
    image = Image.frombytes("RGB", shot.size, shot.rgb)
    raw = pytesseract.image_to_string(image)
    return normalize_text(raw)


def diff_size(old: str, new: str) -> int:
    matcher = difflib.SequenceMatcher(a=old, b=new)
    changed = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            changed += (i2 - i1) + (j2 - j1)
    return changed


def local_analysis(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    word_count = len(re.findall(r"\b\w+\b", text))

    alerts = []
    alert_patterns = {
        "error": r"\berror\b|\bexception\b|\bfail(?:ed|ure)?\b",
        "auth": r"\blogin\b|\bpassword\b|\bauth(?:entication)?\b",
        "payment": r"\bpayment\b|\bcard\b|\bbilling\b",
        "deadline": r"\bdue\b|\bdeadline\b|\bexpires?\b",
    }
    lower = text.lower()
    for label, pattern in alert_patterns.items():
        if re.search(pattern, lower):
            alerts.append(label)

    summary = []
    summary.append(f"{len(lines)} non-empty lines, ~{word_count} words.")
    if lines:
        summary.append(f"Top line: {lines[0][:140]}")
    if alerts:
        summary.append("Detected themes: " + ", ".join(alerts))
    else:
        summary.append("No high-signal keywords detected.")
    return " ".join(summary)


def openai_analysis(text: str, model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package not installed. Run: pip install -r scripts/requirements-screen-monitor.txt") from exc

    client = OpenAI(api_key=api_key)
    prompt = (
        "You analyze live OCR text from a user's screen. "
        "Return concise bullets: 1) what changed, 2) likely intent/context, "
        "3) any actionable next steps. Keep it under 90 words.\n\n"
        f"OCR text:\n{text[:12000]}"
    )
    resp = client.responses.create(
        model=model,
        input=prompt,
        temperature=0.2,
    )
    return (resp.output_text or "(no analysis returned)").strip()


def analyze(text: str, model: str) -> str:
    if model == "local":
        return local_analysis(text)
    return openai_analysis(text, model)


def print_block(title: str, body: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] {title}")
    print("-" * 80)
    print(body if body else "(empty)")


def run(config: AnalysisConfig) -> None:
    previous = ""
    print("Starting screen text monitor. Press Ctrl+C to stop.")

    while True:
        current = capture_ocr_text()
        changed = diff_size(previous, current)

        if changed >= config.min_change_chars:
            if config.show_raw_text:
                print_block("OCR text", current)
            try:
                analysis = analyze(current, config.model)
                print_block("Analysis", analysis)
            except Exception as exc:  # pragma: no cover - runtime fallback
                print_block("Analysis error", str(exc))

            previous = current
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No meaningful change ({changed} chars).")

        time.sleep(config.interval)


def parse_args(argv: Iterable[str]) -> AnalysisConfig:
    parser = argparse.ArgumentParser(description="Continuously OCR screen text and analyze updates.")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between captures (default: 2.0)")
    parser.add_argument(
        "--min-change-chars",
        type=int,
        default=50,
        help="Minimum text delta before re-analysis (default: 50)",
    )
    parser.add_argument("--show-raw-text", action="store_true", help="Print OCR text whenever analysis runs")
    parser.add_argument(
        "--model",
        default="local",
        help="Analysis mode: 'local' (default) or an OpenAI model like 'gpt-4.1-mini'",
    )

    args = parser.parse_args(list(argv))
    return AnalysisConfig(
        interval=max(0.5, args.interval),
        min_change_chars=max(0, args.min_change_chars),
        show_raw_text=args.show_raw_text,
        model=args.model,
    )


def main() -> int:
    config = parse_args(sys.argv[1:])
    try:
        run(config)
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
