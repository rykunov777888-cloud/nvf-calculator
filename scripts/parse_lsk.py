"""Parse cities and snow regions from lsk-lskos.ru/sr.

The page contains a table built from
СП 20.13330.2016 (Изменение № 2, таблица 10.1) — снеговые районы по карте 1.

Usage:
    python3 scripts/parse_lsk.py

Writes outputs/lsk-lskos-cities.json with a list of:
    {
      "city": "Москва",
      "region": "г. Москва",
      "snow_region": "III",
      "sg_kpa": 1.5,
      "source": "lsk-lskos.ru/sr (СП 20.13330.2016, Изм. №2, табл. 10.1)"
    }
"""

from __future__ import annotations

import html as htmllib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "outputs" / "lsk-lskos-cities.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

URL = "https://lsk-lskos.ru/sr"
SOURCE_LABEL = "lsk-lskos.ru/sr (СП 20.13330.2016, Изм. №2, табл. 10.1)"


def fetch_html(url: str = URL) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; nvf-calculator/0.1)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_html(s: str) -> str:
    return htmllib.unescape(re.sub(r"<[^>]+>", "", s)).replace("\xa0", " ").strip()


def parse(html: str) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    tr_pat = re.compile(
        r'<tr role="row" style="display: table-row;">.*?</tr>',
        re.DOTALL,
    )
    td_pat = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)

    for tr in tr_pat.findall(html):
        tds = td_pat.findall(tr)
        if len(tds) < 4:
            continue
        city = strip_html(tds[0])
        region = strip_html(tds[1])
        snow_region = strip_html(tds[2])
        sg_text = strip_html(tds[3]).replace(",", ".")
        try:
            sg_kpa: float | None = float(sg_text)
        except ValueError:
            sg_kpa = None

        key = (city, region)
        if not city or key in seen:
            continue
        seen.add(key)

        rows.append(
            {
                "city": city,
                "region": region,
                "snow_region": snow_region,
                "sg_kpa": sg_kpa,
                "source": SOURCE_LABEL,
            }
        )

    rows.sort(key=lambda r: (r["region"], r["city"]))
    return rows


def main() -> int:
    html = fetch_html()
    rows = parse(html)
    print(f"Parsed {len(rows)} unique cities from {URL}")
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"Saved to {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
