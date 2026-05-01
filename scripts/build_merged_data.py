"""
Объединённая база климатических параметров (205-база + extended-1065).

Принципы:
- Источник базовых записей: extended (1065 городов, lsk-lskos + ese.pro + Nominatim).
- Записи 205-базы, не вошедшие в extended (другая привязка региона), добавляются отдельно.
- К каждой записи добавляется булев флаг `inSP131` — попадает ли город в список
  СП 131.13330.2020 (Строительная климатология). Используется два независимых
  сигнала: (а) ese.pro вернул данные СП 131 (cold/warm/monthly), (б) имя города
  совпало (целиком или по префиксу) с именем из таблицы 3.1 СП 131. Истина =
  любой из сигналов сработал.
- Округлений нет: точные значения как в ese.pro.
- Финальные файлы: src/data/regions/settlements-climate-merged.json
                  data-source/settlements-climate-merged-master.xlsx
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

BASE_PATH = ROOT / "src" / "data" / "regions" / "settlements-climate.json"
EXT_PATH  = ROOT / "src" / "data" / "regions" / "settlements-climate-extended.json"
SP131_PATH = ROOT / "outputs" / "sp131-cities.json"

OUT_JSON = ROOT / "src" / "data" / "regions" / "settlements-climate-merged.json"
OUT_XLSX = ROOT / "data-source" / "settlements-climate-merged-master.xlsx"


def normalize(s: str) -> str:
    """Lowercased, trimmed, non-letters dropped — для сравнения имён."""
    return re.sub(r"[^а-яёa-z\-]", "", (s or "").lower())


def build_sp131_matcher(sp131_names: list[str]):
    """Возвращает функцию match(city_name) -> bool по списку СП 131."""
    norm_names = sorted({normalize(n) for n in sp131_names if n}, key=lambda x: -len(x))
    norm_set = set(norm_names)

    def match(city: str) -> bool:
        n = normalize(city)
        if not n:
            return False
        if n in norm_set:
            return True
        # обработка усечений в PDF (напр. "Санкт-Пете" ↔ "Санкт-Петербург"):
        # допустим обоюдное соответствие префиксом длиной >= 7
        for ref in norm_names:
            if len(ref) < 7:
                continue
            if n.startswith(ref) or ref.startswith(n):
                if min(len(n), len(ref)) >= 7:
                    return True
        return False

    return match


def has_sp131_data(s: dict[str, Any]) -> bool:
    """Считаем, что ese.pro вернул СП 131 данные если есть coldPeriod / monthlyTemps."""
    if (s.get("coldPeriod") or {}).get("tempColdest5days092") is not None:
        return True
    if (s.get("warmPeriod") or {}).get("temp092") is not None:
        return True
    mt = s.get("monthlyTemps") or {}
    by = mt.get("byMonth") or []
    return any(v is not None for v in by)


def main() -> None:
    base = json.load(BASE_PATH.open("r", encoding="utf-8"))
    ext  = json.load(EXT_PATH.open("r", encoding="utf-8"))
    sp131_names = json.load(SP131_PATH.open("r", encoding="utf-8"))
    is_sp131 = build_sp131_matcher(sp131_names)

    # Index extended by (settlement_norm, region_norm)
    ext_pair_set = {
        (normalize(s["settlement"]), normalize(s["region"]))
        for s in ext
    }
    ext_settlement_set = {normalize(s["settlement"]) for s in ext}

    # 205 base records that are not present in extended (by city+region pair)
    base_extra: list[dict[str, Any]] = []
    for s in base:
        pair = (normalize(s["settlement"]), normalize(s["region"]))
        if pair not in ext_pair_set:
            base_extra.append(s)

    merged: list[dict[str, Any]] = []

    # 1) extended (1065)
    for s in ext:
        rec = dict(s)
        rec["inSP131"] = bool(
            is_sp131(s["settlement"]) or has_sp131_data(s)
        )
        rec["sourceList"] = "extended-1065"
        merged.append(rec)

    # 2) base extras (32)
    for s in base_extra:
        rec = dict(s)
        # 205 base has different fields; keep its native shape but ensure terrain etc.
        rec["inSP131"] = bool(
            is_sp131(s["settlement"]) or has_sp131_data(s)
        )
        rec["sourceList"] = "base-205"
        # Add empty coordinates field so JSON shape is consistent
        if "coordinates" not in rec:
            rec["coordinates"] = {"lat": None, "lon": None,
                                   "source": None, "status": "requires_verification"}
        merged.append(rec)

    # Stats
    n_total = len(merged)
    n_sp131 = sum(1 for s in merged if s["inSP131"])
    n_geo = sum(1 for s in merged if (s.get("coordinates") or {}).get("lat") is not None)
    n_verified = sum(1 for s in merged if s.get("dataStatus") == "verified")
    n_partial  = sum(1 for s in merged if s.get("dataStatus") == "partial")
    n_pending  = sum(1 for s in merged if s.get("dataStatus") == "requires_verification")

    print(f"merged total : {n_total}")
    print(f"  base-205   : {len(base_extra)}")
    print(f"  ext-1065   : {len(ext)}")
    print(f"  inSP131=true: {n_sp131}")
    print(f"  with coords: {n_geo}")
    print(f"  verified   : {n_verified}")
    print(f"  partial    : {n_partial}")
    print(f"  pending    : {n_pending}")

    # Sort: inSP131 first, then by region+settlement
    merged.sort(key=lambda r: (
        not r["inSP131"],
        r.get("region") or "",
        r.get("settlement") or "",
    ))

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"json: {OUT_JSON}")

    write_xlsx(merged, OUT_XLSX)
    print(f"xlsx: {OUT_XLSX}")


def write_xlsx(records: list[dict[str, Any]], path: Path) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()

    # Sheet 1: master
    ws = wb.active
    assert ws is not None
    ws.title = "01_merged_master"
    headers = [
        "in_sp131", "source_list",
        "id", "country", "region", "settlement", "settlement_type",
        "lat", "lon",
        "snow_region", "sg_kpa", "snow_source", "snow_status",
        "wind_region", "w0_kpa", "wind_source", "wind_status",
        "ice_region", "ice_thickness_mm", "ice_source", "ice_status",
        "seismic_points", "seismic_source", "seismic_status",
        "data_status", "comment",
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    yes_fill = PatternFill(start_color="D9F2D9", end_color="D9F2D9", fill_type="solid")

    for s in records:
        snow = s.get("snow") or {}
        wind = s.get("wind") or {}
        ice  = s.get("ice")  or {}
        seismic = s.get("seismic") or {}
        coords = s.get("coordinates") or {}
        row = [
            "да" if s.get("inSP131") else "нет",
            s.get("sourceList"),
            s.get("id"), s.get("country"), s.get("region"),
            s.get("settlement"), s.get("settlementType"),
            coords.get("lat"), coords.get("lon"),
            snow.get("region"), snow.get("sgKpa"),
            snow.get("source"), snow.get("status"),
            wind.get("region"), wind.get("w0Kpa"),
            wind.get("source"), wind.get("status"),
            ice.get("region"), ice.get("iceThicknessMm"),
            ice.get("source"), ice.get("status"),
            seismic.get("points"), seismic.get("source"), seismic.get("status"),
            s.get("dataStatus"), s.get("comment"),
        ]
        ws.append(row)
        if s.get("inSP131"):
            for cell in ws[ws.max_row]:
                cell.fill = yes_fill

    # Auto-filter on header row
    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = "C2"

    # Column widths
    widths = {
        "A": 9, "B": 14, "C": 30, "D": 9, "E": 30, "F": 28, "G": 12,
        "H": 10, "I": 10, "J": 7, "K": 9, "L": 24, "M": 10,
        "N": 7, "O": 9, "P": 24, "Q": 10,
        "R": 7, "S": 9, "T": 24, "U": 10,
        "V": 8, "W": 24, "X": 10, "Y": 10, "Z": 60,
    }
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    # Sheet 2: only inSP131 (subset for filtering convenience)
    ws2 = wb.create_sheet("02_only_in_sp131")
    ws2.append(headers)
    for cell in ws2[1]:
        cell.font = Font(bold=True)
    for s in records:
        if not s.get("inSP131"):
            continue
        snow = s.get("snow") or {}
        wind = s.get("wind") or {}
        ice  = s.get("ice")  or {}
        seismic = s.get("seismic") or {}
        coords = s.get("coordinates") or {}
        ws2.append([
            "да", s.get("sourceList"),
            s.get("id"), s.get("country"), s.get("region"),
            s.get("settlement"), s.get("settlementType"),
            coords.get("lat"), coords.get("lon"),
            snow.get("region"), snow.get("sgKpa"),
            snow.get("source"), snow.get("status"),
            wind.get("region"), wind.get("w0Kpa"),
            wind.get("source"), wind.get("status"),
            ice.get("region"), ice.get("iceThicknessMm"),
            ice.get("source"), ice.get("status"),
            seismic.get("points"), seismic.get("source"), seismic.get("status"),
            s.get("dataStatus"), s.get("comment"),
        ])
    ws2.auto_filter.ref = ws2.dimensions
    ws2.freeze_panes = "C2"
    for col, w in widths.items():
        ws2.column_dimensions[col].width = w

    # Sheet 3: source plan
    ws3 = wb.create_sheet("03_sources")
    ws3.append(["Источник", "Назначение", "Покрытие"])
    for cell in ws3[1]:
        cell.font = Font(bold=True)
    rows = [
        ["lsk-lskos.ru/sr",
         "Реестр городов + Sg по СП 20 Изм. №2 табл. 10.1",
         "1065 уникальных городов"],
        ["ese.pro/tools/calculatory/klimaticheskie-nagruzki/",
         "Снег / ветер / гололёд / сейсмика / СП 22 / СП 131",
         "Полный пакет для всех городов из реестра"],
        ["OSM Nominatim",
         "Координаты lat/lon",
         "1018 / 1065 в extended"],
        ["СП 131.13330.2020 (Строительная климатология)",
         "Список ~452 городов с климатическими параметрами",
         "Используется как ground-truth для флага inSP131"],
        ["СП 20.13330.2016 Изм. №2",
         "Снеговое/ветровое/гололёдное районирование",
         "Карты + табл. 10.1 / 11.1 / 12.1"],
    ]
    for r in rows:
        ws3.append(r)
    ws3.column_dimensions["A"].width = 40
    ws3.column_dimensions["B"].width = 50
    ws3.column_dimensions["C"].width = 30

    wb.save(path)


if __name__ == "__main__":
    main()
