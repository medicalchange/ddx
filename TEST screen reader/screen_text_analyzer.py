#!/usr/bin/env python3
"""
Continuously read on-screen text via OCR and provide ongoing analysis.

Works best on macOS/Windows with:
  - Python packages: pillow, pytesseract
  - System OCR binary: tesseract
"""

from __future__ import annotations

import argparse
import re
import signal
import sys
import time
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from typing import Deque

from PIL import ImageGrab, ImageOps
import pytesseract


STOP = False
STOP_WORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "you",
    "this",
    "from",
    "have",
    "are",
    "your",
    "was",
    "will",
    "can",
    "all",
    "not",
    "but",
    "has",
    "its",
    "they",
    "what",
    "when",
    "where",
    "how",
    "why",
    "then",
    "into",
    "about",
    "there",
    "their",
    "them",
    "just",
    "more",
    "some",
    "out",
    "any",
}


@dataclass
class Analysis:
    char_count: int
    word_count: int
    top_words: list[tuple[str, int]]
    urls: list[str]
    emails: list[str]
    todo_signals: list[str]
    question_count: int
    urgency_hits: list[str]


def handle_sigint(_sig: int, _frame: object) -> None:
    global STOP
    STOP = True


def preprocess_image(img):
    gray = ImageOps.grayscale(img)
    return ImageOps.autocontrast(gray)


def capture_screen_text(region: tuple[int, int, int, int] | None = None) -> str:
    img = ImageGrab.grab(bbox=region)
    img = preprocess_image(img)
    return pytesseract.image_to_string(img)


def clean_text(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def analyze_text(text: str) -> Analysis:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{1,}", text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    counts = Counter(filtered)
    top_words = counts.most_common(8)

    urls = sorted(set(re.findall(r"https?://[^\s)]+", text)))
    emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)))

    todo_signals = sorted(
        set(
            m.group(0)
            for m in re.finditer(
                r"\b(todo|to do|fixme|action item|deadline|due|follow up|next step)\b",
                text.lower(),
            )
        )
    )

    urgency_hits = sorted(
        set(
            m.group(0)
            for m in re.finditer(r"\b(urgent|asap|immediately|critical|blocker|high priority)\b", text.lower())
        )
    )
    question_count = text.count("?")

    return Analysis(
        char_count=len(text),
        word_count=len(words),
        top_words=top_words,
        urls=urls,
        emails=emails,
        todo_signals=todo_signals,
        question_count=question_count,
        urgency_hits=urgency_hits,
    )


def summarize_recent(history: Deque[str]) -> str:
    if not history:
        return "No text captured yet."
    combined = "\n".join(history)
    words = re.findall(r"[A-Za-z][A-Za-z'-]{1,}", combined.lower())
    counts = Counter(w for w in words if w not in STOP_WORDS)
    top = ", ".join([f"{w}({n})" for w, n in counts.most_common(6)]) or "n/a"
    return f"Recent topic terms: {top}"


def parse_region(region: str | None) -> tuple[int, int, int, int] | None:
    if not region:
        return None
    parts = [p.strip() for p in region.split(",")]
    if len(parts) != 4:
        raise ValueError("Region must be x1,y1,x2,y2")
    x1, y1, x2, y2 = [int(v) for v in parts]
    if not (x2 > x1 and y2 > y1):
        raise ValueError("Region must satisfy x2>x1 and y2>y1")
    return (x1, y1, x2, y2)


def print_analysis(a: Analysis, snippet: str, recent_summary: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] Screen text updated")
    print("-" * 70)
    print(f"Chars: {a.char_count} | Words: {a.word_count} | Questions: {a.question_count}")
    if a.top_words:
        print("Top terms:", ", ".join(f"{w}:{c}" for w, c in a.top_words))
    if a.urls:
        print("URLs:", ", ".join(a.urls[:5]))
    if a.emails:
        print("Emails:", ", ".join(a.emails[:5]))
    if a.todo_signals:
        print("Task signals:", ", ".join(a.todo_signals))
    if a.urgency_hits:
        print("Urgency signals:", ", ".join(a.urgency_hits))
    print(recent_summary)
    print("Snippet:")
    print(snippet[:700] if snippet else "(no OCR text)")
    print("-" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(description="Live screen OCR + ongoing text analysis")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between captures (default: 2.0)")
    parser.add_argument(
        "--region",
        type=str,
        default=None,
        help="Optional OCR region: x1,y1,x2,y2 (screen coords)",
    )
    parser.add_argument("--history", type=int, default=8, help="How many recent captures to keep (default: 8)")
    args = parser.parse_args()

    if args.interval < 0.5:
        print("Interval too small. Use >= 0.5 seconds.", file=sys.stderr)
        return 2

    try:
        region = parse_region(args.region)
    except ValueError as e:
        print(f"Invalid --region: {e}", file=sys.stderr)
        return 2

    signal.signal(signal.SIGINT, handle_sigint)

    print("Starting live screen OCR. Press Ctrl+C to stop.")
    if region:
        print(f"Using region: {region}")

    prev_digest = ""
    recent_text: Deque[str] = deque(maxlen=args.history)

    while not STOP:
        try:
            raw = capture_screen_text(region=region)
        except Exception as e:  # noqa: BLE001
            print(f"OCR/capture error: {e}", file=sys.stderr)
            print("Tip: On macOS, grant Screen Recording permission and install tesseract.", file=sys.stderr)
            time.sleep(max(args.interval, 2.0))
            continue

        cleaned = clean_text(raw)
        digest = sha1(cleaned.encode("utf-8")).hexdigest() if cleaned else ""

        if digest and digest != prev_digest:
            prev_digest = digest
            recent_text.append(cleaned)
            analysis = analyze_text(cleaned)
            recent_summary = summarize_recent(recent_text)
            print_analysis(analysis, cleaned, recent_summary)

        time.sleep(args.interval)

    print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
