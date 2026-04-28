"""Scrape ese.pro climate calc for a batch of cities.

Usage:
    python3 scripts/scrape_ese.py [--limit N] [--start I]

Reads `src/data/regions/settlements-climate.json` for the target list of
cities (uses `settlement` field). For each city:
  1. opens https://ese.pro/tools/calculatory/klimaticheskie-nagruzki/
  2. types the city name
  3. clicks the first Dadata-style suggestion
  4. waits for the result panel
  5. parses the visible text via parse_ese.parse_ese_text()
  6. appends a row into outputs/ese-data.json (incremental, resumable)

Designed to be resumable: if outputs/ese-data.json already has a row for
the given settlement id, it is skipped.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from parse_ese import parse_ese_text  # noqa: E402

URL = "https://ese.pro/tools/calculatory/klimaticheskie-nagruzki/"
SETTLEMENTS_PATH = ROOT / "src" / "data" / "regions" / "settlements-climate.json"
OUT_PATH = ROOT / "outputs" / "ese-data.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_existing() -> Dict[str, Dict[str, Any]]:
    if OUT_PATH.exists():
        with OUT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save(state: Dict[str, Dict[str, Any]]) -> None:
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def scrape_city(page, city: str) -> Optional[Dict[str, Any]]:
    """Type city, click first suggestion, return parsed dict or None."""
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    # type in input
    inp = page.locator("#ccl-q")
    inp.click()
    inp.fill(city)
    page.wait_for_timeout(2000)

    # click first suggestion
    sug = page.locator(".climatic-section__suggestions-item").first
    try:
        sug.wait_for(timeout=8000)
    except PWTimeout:
        return None
    sug.click()

    # wait for either snow value or some result text
    deadline = time.time() + 15
    text = ""
    while time.time() < deadline:
        page.wait_for_timeout(1500)
        text = page.locator("body").inner_text()
        if "Снеговая нагрузка" in text and "Гололедная" in text:
            break
    if "Снеговая нагрузка" not in text:
        return None

    return parse_ese_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N settlements.")
    parser.add_argument("--start", type=int, default=0,
                        help="Skip the first N settlements.")
    parser.add_argument("--ids", type=str, default=None,
                        help="Comma-separated list of settlement ids to process (overrides --limit/--start).")
    parser.add_argument("--headed", action="store_true",
                        help="Run with a visible browser.")
    parser.add_argument("--force", action="store_true",
                        help="Re-scrape even if data already exists.")
    args = parser.parse_args()

    settlements: List[Dict[str, Any]] = json.load(SETTLEMENTS_PATH.open("r", encoding="utf-8"))

    if args.ids:
        wanted = set(args.ids.split(","))
        settlements = [s for s in settlements if s["id"] in wanted]
    else:
        if args.start:
            settlements = settlements[args.start:]
        if args.limit:
            settlements = settlements[: args.limit]

    state = load_existing()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(viewport={"width": 1600, "height": 900})
        page = ctx.new_page()

        for i, s in enumerate(settlements):
            sid = s["id"]
            settlement_name = s["settlement"]
            if not args.force and sid in state and state[sid].get("data", {}).get("loads", {}).get("snow", {}).get("kpa") is not None:
                # already scraped
                continue
            t0 = time.time()
            try:
                parsed = scrape_city(page, settlement_name)
            except Exception as e:
                parsed = None
                err = repr(e)[:200]
            else:
                err = None

            row: Dict[str, Any] = {
                "id": sid,
                "settlement": settlement_name,
                "region": s["region"],
                "scrapedAt": int(time.time()),
                "error": err,
                "data": parsed,
            }
            state[sid] = row
            save(state)
            dt = time.time() - t0
            ok = parsed is not None and parsed["loads"]["snow"]["kpa"] is not None
            print(f"[{i+1}/{len(settlements)}] {sid} ({settlement_name}) ok={ok} t={dt:.1f}s err={err}",
                  flush=True)

        browser.close()


if __name__ == "__main__":
    main()
