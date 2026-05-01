"""Scrape ese.pro climate calc for the EXTENDED list (1065 cities).

Reads outputs/lsk-lskos-cities.json (parsed from lsk-lskos.ru/sr).
For each city, opens https://ese.pro/tools/calculatory/klimaticheskie-nagruzki/,
types `<city>, <region>`, clicks the first Dadata suggestion, and parses
the visible result text via parse_ese.parse_ese_text().

Designed to be resumable. Output: outputs/ese-data-extended.json keyed
by a stable slug id = slugify("<city>__<region>"). If a row already has
loads.snow.kpa, it is skipped.

Usage:
    python3 scripts/scrape_ese_extended.py [--limit N] [--start I] [--headed] [--force]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from parse_ese import parse_ese_text  # noqa: E402

URL = "https://ese.pro/tools/calculatory/klimaticheskie-nagruzki/"
IN_PATH = ROOT / "outputs" / "lsk-lskos-cities.json"
OUT_PATH = ROOT / "outputs" / "ese-data-extended.json"
EXISTING_SETTLEMENTS_PATH = ROOT / "src" / "data" / "regions" / "settlements-climate.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

COMMIT_EVERY = 100  # cities

_TRANS = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def slugify(s: str) -> str:
    s = s.strip().lower()
    out = []
    for ch in s:
        if ch in _TRANS:
            out.append(_TRANS[ch])
        elif ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "."):
            out.append("_")
    res = "".join(out)
    res = re.sub(r"_+", "_", res).strip("_")
    return res


def make_id(city: str, region: str) -> str:
    return f"{slugify(city)}__{slugify(region)}"


def load_state() -> Dict[str, Dict[str, Any]]:
    if OUT_PATH.exists():
        return json.load(OUT_PATH.open("r", encoding="utf-8"))
    return {}


def save_state(state: Dict[str, Dict[str, Any]]) -> None:
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def load_existing_skip_set() -> set[tuple[str, str]]:
    """Build a set of (city, region) tuples already verified in 205-city base.

    Matches case-insensitively on settlement+region.
    """
    if not EXISTING_SETTLEMENTS_PATH.exists():
        return set()
    try:
        existing = json.load(EXISTING_SETTLEMENTS_PATH.open("r", encoding="utf-8"))
    except Exception:
        return set()
    skip: set[tuple[str, str]] = set()
    for s in existing:
        # Only skip if data is verified - no point re-scraping if already good
        snow = s.get("snow") or {}
        if snow.get("status") == "verified":
            skip.add((s["settlement"].strip().lower(), s["region"].strip().lower()))
    return skip


def git_commit_push(milestone: int) -> None:
    """Commit and push current progress to remote so a restarted session can resume."""
    try:
        subprocess.run(
            ["git", "add", str(OUT_PATH.relative_to(ROOT))],
            cwd=ROOT, check=True, capture_output=True,
        )
        msg = f"Скрейпер ese.pro extended: автокоммит после {milestone} городов"
        r = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=ROOT, capture_output=True, text=True,
        )
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            print(f"[git] commit failed: {r.stderr.strip()}", flush=True)
            return
        r = subprocess.run(
            ["git", "push"], cwd=ROOT, capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"[git] push failed: {r.stderr.strip()[:200]}", flush=True)
        else:
            print(f"[git] pushed milestone={milestone}", flush=True)
    except Exception as e:
        print(f"[git] error: {e}", flush=True)


def scrape_one(page, query: str) -> Optional[Dict[str, Any]]:
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    inp = page.locator("#ccl-q")
    inp.click()
    inp.fill(query)
    page.wait_for_timeout(2000)

    sug = page.locator(".climatic-section__suggestions-item").first
    try:
        sug.wait_for(timeout=8000)
    except PWTimeout:
        return None
    sug.click()

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cities: List[Dict[str, Any]] = json.load(IN_PATH.open("r", encoding="utf-8"))

    # Filter out cities that are already verified in the 205-city base
    skip_set = load_existing_skip_set()
    if skip_set:
        before = len(cities)
        cities = [
            c for c in cities
            if (c["city"].strip().lower(), c["region"].strip().lower()) not in skip_set
        ]
        print(f"[filter] skipped {before - len(cities)} already verified cities; "
              f"remaining {len(cities)}", flush=True)

    if args.start:
        cities = cities[args.start:]
    if args.limit:
        cities = cities[: args.limit]

    state = load_state()
    total = len(cities)
    ok_cnt = 0
    fail_cnt = 0
    skip_cnt = 0
    last_commit_at = 0

    with sync_playwright() as p:
        def make_browser():
            br = p.chromium.launch(headless=not args.headed)
            ct = br.new_context(viewport={"width": 1600, "height": 900})
            pg = ct.new_page()
            return br, ct, pg

        browser, ctx, page = make_browser()
        cities_since_restart = 0

        for i, c in enumerate(cities):
            city = c["city"]
            region = c["region"]
            sid = make_id(city, region)

            already = state.get(sid)
            if not args.force and already and already.get("data") is not None:
                snow_kpa = (
                    already.get("data", {})
                    .get("loads", {})
                    .get("snow", {})
                    .get("kpa")
                )
                if snow_kpa is not None:
                    skip_cnt += 1
                    continue

            # Periodically recycle browser to avoid memory accumulation crashes
            if cities_since_restart >= 200:
                try:
                    browser.close()
                except Exception:
                    pass
                browser, ctx, page = make_browser()
                cities_since_restart = 0
                print("[browser] recycled after 200 cities", flush=True)

            t0 = time.time()
            err = None
            parsed = None
            # Try city+region first, then plain city, then city+", Россия"
            queries = [f"{city}, {region}", city, f"{city}, Россия"]
            for q in queries:
                try:
                    parsed = scrape_one(page, q)
                except Exception as e:
                    err = repr(e)[:200]
                    parsed = None
                    # If page/browser crashed, recreate them and retry once
                    if "Page crashed" in err or "Target closed" in err or "TargetClosed" in err:
                        try:
                            browser.close()
                        except Exception:
                            pass
                        browser, ctx, page = make_browser()
                        cities_since_restart = 0
                        print(f"[browser] restarted after crash on {sid}", flush=True)
                        try:
                            parsed = scrape_one(page, q)
                            err = None
                        except Exception as e2:
                            err = repr(e2)[:200]
                            parsed = None
                if parsed and parsed.get("loads", {}).get("snow", {}).get("kpa") is not None:
                    err = None
                    break
            cities_since_restart += 1

            row = {
                "id": sid,
                "city": city,
                "region": region,
                "snow_region_lsk": c.get("snow_region"),
                "sg_kpa_lsk": c.get("sg_kpa"),
                "scrapedAt": int(time.time()),
                "error": err,
                "data": parsed,
            }
            state[sid] = row

            ok = parsed is not None and parsed.get("loads", {}).get("snow", {}).get("kpa") is not None
            if ok:
                ok_cnt += 1
            else:
                fail_cnt += 1

            # Save every 5 records to avoid losing progress on crash
            if (i + 1) % 5 == 0:
                save_state(state)

            dt = time.time() - t0
            print(
                f"[{i+1}/{total}] {sid} ok={ok} t={dt:.1f}s "
                f"(ok={ok_cnt} fail={fail_cnt} skip={skip_cnt}) err={err}",
                flush=True,
            )

            # Auto-commit + push every COMMIT_EVERY new cities so progress
            # survives a session restart.
            done_cnt = ok_cnt + fail_cnt
            if done_cnt and done_cnt - last_commit_at >= COMMIT_EVERY:
                save_state(state)
                git_commit_push(done_cnt)
                last_commit_at = done_cnt

        save_state(state)
        if (ok_cnt + fail_cnt) > last_commit_at:
            git_commit_push(ok_cnt + fail_cnt)
        browser.close()

    print(f"DONE total={total} ok={ok_cnt} fail={fail_cnt} skip={skip_cnt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
