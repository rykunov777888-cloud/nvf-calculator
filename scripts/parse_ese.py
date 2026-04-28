"""Parse text dump of ese.pro climate calculator result page.

Used by `scrape_ese.py` to extract structured climate data after typing a
city into the ese.pro calculator and clicking the first suggestion.

The input is plain page text (page.locator("body").inner_text() in Playwright).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


_SNOW_DISTRICTS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII"}
_WIND_DISTRICTS = {"Ia", "I", "II", "III", "IV", "V", "VI", "VII"}
_ICE_DISTRICTS = {"I", "II", "III", "IV", "V"}


def _to_float(s: str) -> Optional[float]:
    s = s.strip().replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def _to_int(s: str) -> Optional[int]:
    s = s.strip().replace(",", ".")
    m = re.search(r"-?\d+", s)
    return int(m.group(0)) if m else None


def parse_ese_text(text: str) -> Dict[str, Any]:
    """Parse the body text of an ese.pro climate calc page into a dict.

    Returns a dict with keys:
        loads.snow.{kpa, region}
        loads.wind.{kpa, region}
        loads.ice.{mm, region}
        seismic.{mapA, mapB, mapC}
        frostDepth.{loamy, sandyFine, sandyCoarse, coarseFragmental} (m)
        cold.{tempColdestDay098, tempColdestDay092,
              tempColdest5days098, tempColdest5days092,
              temp094, absMin, dailyAmplitude,
              durationLe0, meanLe0,
              durationLe8, meanLe8,
              durationLe10, meanLe10,
              humidityCold, humidityCold15,
              precipNovMar, prevailingWindDecFeb,
              maxWindJan, meanWindLe8}
        warm.{barometric, temp095, temp099, meanMaxTempWarmMonth, absMax,
              dailyAmplitude, humidityWarm, humidityWarm15,
              precipAprOct, dailyMaxPrecip, prevailingWindJunAug,
              minWindJul}
        monthlyTemps: list of 13 values (Jan..Dec, Year) or None
    """
    out: Dict[str, Any] = {
        "loads": {
            "snow": {"kpa": None, "region": None},
            "wind": {"kpa": None, "region": None},
            "ice": {"mm": None, "region": None},
        },
        "seismic": {"mapA": None, "mapB": None, "mapC": None},
        "frostDepth": {
            "loamy": None,
            "sandyFine": None,
            "sandyCoarse": None,
            "coarseFragmental": None,
        },
        "cold": {},
        "warm": {},
        "monthlyTemps": None,
    }

    # ------------------------------------------------------------------
    # Loads (snow/wind/ice)
    # ------------------------------------------------------------------
    # Snow line shape varies; the value & district may end up on different
    # lines because of long table layout. We match on the labeled key.
    m = re.search(
        r"Снеговая нагрузка,\s*кПа\s+([\d.,]+)[\s\S]{0,120}?(VIII|VII|VI|V|IV|III|II|I)(?=\s|$)",
        text,
    )
    if m:
        out["loads"]["snow"]["kpa"] = _to_float(m.group(1))
        district = m.group(2).strip()
        if district in _SNOW_DISTRICTS:
            out["loads"]["snow"]["region"] = district

    m = re.search(
        r"Ветровая нагрузка,\s*кПа\s+([\d.,]+)[\s\S]{0,80}?(Ia|VII|VI|V|IV|III|II|I)(?=\s|$)",
        text,
    )
    if m:
        out["loads"]["wind"]["kpa"] = _to_float(m.group(1))
        d = m.group(2).strip()
        if d in _WIND_DISTRICTS:
            out["loads"]["wind"]["region"] = d

    m = re.search(
        r"Гололедная нагрузка,\s*мм\s+(?:Не менее\s+)?([\d.,]+)[\s\S]{0,80}?(V|IV|III|II|I)(?=\s|$)",
        text,
    )
    if m:
        out["loads"]["ice"]["mm"] = _to_float(m.group(1))
        d = m.group(2).strip()
        if d in _ICE_DISTRICTS:
            out["loads"]["ice"]["region"] = d

    # ------------------------------------------------------------------
    # Seismic
    # ------------------------------------------------------------------
    for letter, key in [("А", "mapA"), ("В", "mapB"), ("С", "mapC")]:
        m = re.search(
            rf"Карта\s+{letter}\s+по\s+ОСР-2015\s+(\d+)",
            text,
        )
        if m:
            out["seismic"][key] = int(m.group(1))

    # ------------------------------------------------------------------
    # Frost depth (norm. only — расчётная требует доп. ввода)
    # ------------------------------------------------------------------
    frost_map = [
        ("Суглинки и глина", "loamy"),
        ("Супесь, пески мелкие и пылеватые", "sandyFine"),
        ("Пески гравелистые, крупные и средней крупности", "sandyCoarse"),
        ("Крупнообломочные грунты", "coarseFragmental"),
    ]
    for label, key in frost_map:
        m = re.search(
            rf"{re.escape(label)}\s+([\d.,]+)",
            text,
        )
        if m:
            out["frostDepth"][key] = _to_float(m.group(1))

    # ------------------------------------------------------------------
    # Cold period (СП 131.13330)
    # ------------------------------------------------------------------
    m = re.search(
        r"Температура воздуха наиболее холодных суток,\s*ºС,\s*обеспеченностью\s+0[.,]98\s+(-?\d+(?:[.,]\d+)?)\s*\n?\s*0[.,]92\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["cold"]["tempColdestDay098"] = _to_float(m.group(1))
        out["cold"]["tempColdestDay092"] = _to_float(m.group(2))

    m = re.search(
        r"Температура воздуха наиболее холодной пятидневки,\s*ºС,\s*обеспеченностью\s+0[.,]98\s+(-?\d+(?:[.,]\d+)?)\s*\n?\s*0[.,]92\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["cold"]["tempColdest5days098"] = _to_float(m.group(1))
        out["cold"]["tempColdest5days092"] = _to_float(m.group(2))

    m = re.search(
        r"Температура воздуха,\s*ºС,\s*обеспеченностью\s+0[.,]94\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["cold"]["temp094"] = _to_float(m.group(1))

    m = re.search(
        r"Абсолютная минимальная температура воздуха,\s*ºС\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["cold"]["absMin"] = _to_float(m.group(1))

    m = re.search(
        r"Средняя суточная амплитуда температуры воздуха наиболее холодного\s*\n?\s*месяца,\s*ºС\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["cold"]["dailyAmplitude"] = _to_float(m.group(1))

    # ≤0/≤8/≤10
    for thresh, dur_key, mean_key in [
        (0, "durationLe0", "meanLe0"),
        (8, "durationLe8", "meanLe8"),
        (10, "durationLe10", "meanLe10"),
    ]:
        m = re.search(
            rf"≤\s*{thresh}\s*ºС\s+продолжительность\s+(\d+)\s*\n?\s*средняя температура\s+(-?\d+(?:[.,]\d+)?)",
            text,
        )
        if m:
            out["cold"][dur_key] = int(m.group(1))
            out["cold"][mean_key] = _to_float(m.group(2))

    m = re.search(
        r"Средняя месячная относительная влажность воздуха наиболее холодного\s*\n?\s*месяца,\s*%\s+(\d+)",
        text,
    )
    if m:
        out["cold"]["humidityCold"] = int(m.group(1))

    m = re.search(
        r"Средняя месячная относительная влажность воздуха в 15 ч\s*\n?\s*наиболее холодного месяца,\s*%\s+(\d+)",
        text,
    )
    if m:
        out["cold"]["humidityCold15"] = int(m.group(1))

    m = re.search(r"Количество осадков за ноябрь.*?,\s*мм\s+(\d+)", text)
    if m:
        out["cold"]["precipNovMar"] = int(m.group(1))

    m = re.search(
        r"Преобладающее направление ветра за декабрь-февраль\s+(\S+)",
        text,
    )
    if m:
        out["cold"]["prevailingWindDecFeb"] = m.group(1).strip()

    m = re.search(
        r"Максимальная из средних скоростей ветра по румбам за январь,\s*м/с\s+([\d.,]+)",
        text,
    )
    if m:
        out["cold"]["maxWindJan"] = _to_float(m.group(1))

    m = re.search(
        r"Средняя скорость ветра,\s*м/с,\s*за период со средней суточной\s*\n?\s*температурой воздуха ≤ 8 ºС\s+([\d.,]+)",
        text,
    )
    if m:
        out["cold"]["meanWindLe8"] = _to_float(m.group(1))

    # ------------------------------------------------------------------
    # Warm period (СП 131.13330)
    # ------------------------------------------------------------------
    m = re.search(r"Барометрическое давление,\s*гПа\s+(\d+)", text)
    if m:
        out["warm"]["barometric"] = int(m.group(1))

    m = re.search(
        r"Температура воздуха,\s*°С,\s*обеспеченностью\s+0[.,]95\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["warm"]["temp095"] = _to_float(m.group(1))

    m = re.search(
        r"Температура воздуха,\s*°С,\s*обеспеченностью\s+0[.,]99\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["warm"]["temp099"] = _to_float(m.group(1))

    m = re.search(
        r"Средняя максимальная температура воздуха наиболее теплого месяца,\s*°С\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["warm"]["meanMaxTempWarmMonth"] = _to_float(m.group(1))

    m = re.search(
        r"Абсолютная максимальная температура воздуха,\s*°С\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["warm"]["absMax"] = _to_float(m.group(1))

    m = re.search(
        r"Средняя суточная амплитуда температуры воздуха наиболее\s*\n?\s*теплого месяца,\s*°С\s+(-?\d+(?:[.,]\d+)?)",
        text,
    )
    if m:
        out["warm"]["dailyAmplitude"] = _to_float(m.group(1))

    m = re.search(
        r"Средняя месячная относительная влажность воздуха наиболее\s*\n?\s*теплого месяца,\s*%\s+(\d+)",
        text,
    )
    if m:
        out["warm"]["humidityWarm"] = int(m.group(1))

    m = re.search(
        r"Средняя месячная относительная влажность воздуха в 15 ч\s*\n?\s*наиболее теплого месяца,\s*%\s+(\d+)",
        text,
    )
    if m:
        out["warm"]["humidityWarm15"] = int(m.group(1))

    m = re.search(r"Количество осадков за апрель.*?,\s*мм\s+(\d+)", text)
    if m:
        out["warm"]["precipAprOct"] = int(m.group(1))

    m = re.search(r"Суточный максимум осадков,\s*мм\s+(\d+)", text)
    if m:
        out["warm"]["dailyMaxPrecip"] = int(m.group(1))

    m = re.search(
        r"Преобладающее направление ветра за июнь.{0,5}август\s+(\S+)",
        text,
    )
    if m:
        out["warm"]["prevailingWindJunAug"] = m.group(1).strip()

    m = re.search(
        r"Минимальная из средних скоростей ветра по румбам за июль,\s*м/с\s+([\d.,]+)",
        text,
    )
    if m:
        out["warm"]["minWindJul"] = _to_float(m.group(1))

    # ------------------------------------------------------------------
    # Monthly temperatures (13 values: I..XII, Year)
    # ------------------------------------------------------------------
    m = re.search(
        r"I\s+II\s+III\s+IV\s+V\s+VI\s+VII\s+VIII\s+IX\s+X\s+XI\s+XII\s+Год\s*\n?\s*([-\d.,\s]+)",
        text,
    )
    if m:
        nums = re.findall(r"-?\d+(?:[.,]\d+)?", m.group(1))[:13]
        if len(nums) == 13:
            out["monthlyTemps"] = [_to_float(n) for n in nums]

    return out


def main() -> None:  # pragma: no cover
    import json
    import sys
    text = open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ese-text.txt").read()
    print(json.dumps(parse_ese_text(text), ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
