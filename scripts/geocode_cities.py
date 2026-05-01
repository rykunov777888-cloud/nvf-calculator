"""Geocode cities via OSM Nominatim (free, ToS-compliant).

Usage:
    python3 scripts/geocode_cities.py

Reads outputs/lsk-lskos-cities.json. For each city, queries Nominatim:
    https://nominatim.openstreetmap.org/search
        ?q=<city>, <region>, Россия
        &format=json&limit=1&accept-language=ru
Sleeps 1 second between requests (Nominatim usage policy: 1 req/sec).

Writes outputs/geocoded-cities.json. Resumable: if a city already has
a non-null lat in the output, it is skipped.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "outputs" / "lsk-lskos-cities.json"
OUT_PATH = ROOT / "outputs" / "geocoded-cities.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "nvf-calculator/0.1 (https://github.com/rykunov777888-cloud/nvf-calculator)"
SOURCE_LABEL = "OSM Nominatim"
SLEEP_SECONDS = 1.1


def make_key(city: str, region: str) -> str:
    return f"{city}||{region}"


def load_state() -> dict[str, dict]:
    if OUT_PATH.exists():
        return json.load(OUT_PATH.open("r", encoding="utf-8"))
    return {}


def save_state(state: dict[str, dict]) -> None:
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def geocode_one(city: str, region: str) -> dict | None:
    q = f"{city}, {region}, Россия"
    params = {
        "q": q,
        "format": "json",
        "limit": "1",
        "accept-language": "ru",
        "addressdetails": "0",
    }
    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": repr(e)[:200]}

    if not data:
        return None
    item = data[0]
    return {
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "display_name": item.get("display_name"),
    }


def main() -> int:
    cities = json.load(IN_PATH.open("r", encoding="utf-8"))
    state = load_state()
    total = len(cities)
    new = 0
    not_found = 0
    failed = 0

    for i, c in enumerate(cities):
        key = make_key(c["city"], c["region"])
        if key in state and state[key].get("lat") is not None:
            continue

        t0 = time.time()
        result = geocode_one(c["city"], c["region"])
        if result is None:
            state[key] = {
                "city": c["city"],
                "region": c["region"],
                "lat": None,
                "lon": None,
                "source": SOURCE_LABEL,
                "status": "not_found",
            }
            not_found += 1
        elif "error" in result:
            state[key] = {
                "city": c["city"],
                "region": c["region"],
                "lat": None,
                "lon": None,
                "source": SOURCE_LABEL,
                "status": "error",
                "error": result["error"],
            }
            failed += 1
        else:
            state[key] = {
                "city": c["city"],
                "region": c["region"],
                "lat": result["lat"],
                "lon": result["lon"],
                "display_name": result.get("display_name"),
                "source": SOURCE_LABEL,
                "status": "verified",
            }
            new += 1

        if (i + 1) % 25 == 0 or i + 1 == total:
            save_state(state)
            print(
                f"[{i+1}/{total}] new={new} not_found={not_found} failed={failed}",
                flush=True,
            )

        dt = time.time() - t0
        sleep_left = max(0.0, SLEEP_SECONDS - dt)
        if sleep_left > 0:
            time.sleep(sleep_left)

    save_state(state)
    print(f"DONE total={total} new={new} not_found={not_found} failed={failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
