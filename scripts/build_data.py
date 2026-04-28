"""
Скрипт для генерации мастер-таблицы климатических параметров.

Создаёт:
  - src/data/regions/settlements-climate.json
  - data-source/settlements-climate-master.xlsx (4 листа)

ВАЖНО: значения, которых нет в открытых проверенных источниках, оставлены как
null со статусом 'requires_verification'. Не выдумывать значения —
дозаполнять должен инженер с актуальными СП на руках.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "src" / "data" / "regions" / "settlements-climate.json"
XLSX_PATH = ROOT / "data-source" / "settlements-climate-master.xlsx"

SOURCE_SP20_APPENDIX_K = "СП 20.13330.2016, приложение К"
SOURCE_SP20 = "СП 20.13330.2016"
SOURCE_SP14 = "СП 14.13330"
SOURCE_ESE_PRO = (
    "СП 20.13330.2016 / СП 14.13330; сверено через "
    "ese.pro/tools/calculatory/klimaticheskie-nagruzki/"
)

ALLOWED_TERRAIN = ["A", "B", "C"]


def settlement(
    *,
    sid: str,
    region: str,
    name: str,
    settlement_type: str | None = "город",
    snow_region: str | None = None,
    sg_kpa: float | None = None,
    snow_status: str = "requires_verification",
    snow_source: str = SOURCE_SP20_APPENDIX_K,
    wind_region: str | None = None,
    w0_kpa: float | None = None,
    wind_status: str = "requires_verification",
    wind_source: str = SOURCE_SP20,
    ice_region: str | None = None,
    ice_thickness_mm: float | None = None,
    ice_status: str = "requires_verification",
    ice_source: str = SOURCE_SP20,
    seismic_points: int | None = None,
    seismic_status: str = "requires_verification",
    seismic_source: str = SOURCE_SP14,
    data_status: str = "partial",
    comment: str = "",
) -> dict[str, Any]:
    """Сформировать запись населённого пункта."""
    return {
        "id": sid,
        "country": "Россия",
        "region": region,
        "settlement": name,
        "settlementType": settlement_type,
        "snow": {
            "region": snow_region,
            "sgKpa": sg_kpa,
            "source": snow_source,
            "status": snow_status,
        },
        "wind": {
            "region": wind_region,
            "w0Kpa": w0_kpa,
            "source": wind_source,
            "status": wind_status,
        },
        "ice": {
            "region": ice_region,
            "iceThicknessMm": ice_thickness_mm,
            "source": ice_source,
            "status": ice_status,
        },
        "seismic": {
            "points": seismic_points,
            "source": seismic_source,
            "status": seismic_status,
        },
        "terrain": {
            "defaultType": None,
            "allowedTypes": ALLOWED_TERRAIN,
        },
        "manualAllowed": True,
        "expertOverrideAllowed": True,
        "dataStatus": data_status,
        "comment": comment,
    }


# ---------------------------------------------------------------------------
# Стартовые данные.
#
# Заполнены только те значения, которые прямо подтверждены пользователем
# (Челябинск) или легко проверяются по приложению К СП 20.13330.2016 для
# крупнейших городов России. Остальные параметры оставлены null +
# requires_verification — должен заполнить инженер.
# ---------------------------------------------------------------------------

DATA: list[dict[str, Any]] = [
    # ---- 15 контрольных городов из ТЗ ----
    settlement(
        sid="moscow",
        region="г. Москва",
        name="Москва",
        snow_region="III",
        sg_kpa=1.5,
        snow_status="verified",
        snow_source=SOURCE_ESE_PRO,
        wind_region="I",
        w0_kpa=0.23,
        wind_status="verified",
        wind_source=SOURCE_ESE_PRO,
        ice_region="II",
        ice_thickness_mm=5,
        ice_status="verified",
        ice_source=SOURCE_ESE_PRO,
        seismic_points=5,
        seismic_status="verified",
        seismic_source=SOURCE_ESE_PRO,
        data_status="verified",
        comment=(
            "Контрольный город. Все параметры сверены через "
            "ese.pro/tools/calculatory/klimaticheskie-nagruzki/. "
            "Снеговая по прил. К СП 20.13330.2016: район III, Sg=1.5 кПа "
            "(в калькуляторе ese.pro показывается уточнённое значение 1.45 кПа). "
            "Ветровая I (0.23 кПа), гололёдная II (5 мм). "
            "Сейсмика по ОСР-2015 (карты A/B/C по СП 14.13330): 5 баллов."
        ),
    ),
    settlement(
        sid="saint_petersburg",
        region="г. Санкт-Петербург",
        name="Санкт-Петербург",
        snow_region="III",
        sg_kpa=1.5,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="chelyabinsk",
        region="Челябинская область",
        name="Челябинск",
        snow_region="III",
        sg_kpa=1.5,
        snow_status="from_sp20_appendix_k",
        wind_region="II",
        w0_kpa=0.30,
        wind_status="requires_verification",
        ice_region="II",
        ice_thickness_mm=5,
        ice_status="requires_verification",
        comment="Контрольный город. Базовая запись из ТЗ.",
    ),
    settlement(
        sid="yekaterinburg",
        region="Свердловская область",
        name="Екатеринбург",
        snow_region="III",
        sg_kpa=1.5,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="kazan",
        region="Республика Татарстан",
        name="Казань",
        snow_region="IV",
        sg_kpa=2.0,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="novosibirsk",
        region="Новосибирская область",
        name="Новосибирск",
        snow_region="IV",
        sg_kpa=2.0,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="krasnodar",
        region="Краснодарский край",
        name="Краснодар",
        snow_region="II",
        sg_kpa=1.0,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="perm",
        region="Пермский край",
        name="Пермь",
        snow_region="V",
        sg_kpa=2.5,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="ufa",
        region="Республика Башкортостан",
        name="Уфа",
        snow_region="V",
        sg_kpa=2.5,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016 — требует сверки (граница IV/V).",
    ),
    settlement(
        sid="samara",
        region="Самарская область",
        name="Самара",
        snow_region="IV",
        sg_kpa=2.0,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="rostov_on_don",
        region="Ростовская область",
        name="Ростов-на-Дону",
        snow_region="II",
        sg_kpa=1.0,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="tyumen",
        region="Тюменская область",
        name="Тюмень",
        snow_region="III",
        sg_kpa=1.5,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="omsk",
        region="Омская область",
        name="Омск",
        snow_region="III",
        sg_kpa=1.5,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Снег по прил. К СП 20.13330.2016.",
    ),
    settlement(
        sid="vladivostok",
        region="Приморский край",
        name="Владивосток",
        snow_region="II",
        sg_kpa=1.0,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Сейсмика требует сверки по СП 14.13330.",
    ),
    settlement(
        sid="yakutsk",
        region="Республика Саха (Якутия)",
        name="Якутск",
        snow_region="II",
        sg_kpa=1.0,
        snow_status="from_sp20_appendix_k",
        comment="Контрольный город. Сейсмика требует сверки по СП 14.13330.",
    ),
    # ---- Дополнительные регионы (стартовый каркас) ----
    # Snow region пока null + requires_verification, инженер дозаполняет
    # по приложению К СП 20.13330.2016.
    settlement(
        sid="nizhny_novgorod",
        region="Нижегородская область",
        name="Нижний Новгород",
    ),
    settlement(
        sid="krasnoyarsk",
        region="Красноярский край",
        name="Красноярск",
    ),
    settlement(
        sid="voronezh",
        region="Воронежская область",
        name="Воронеж",
    ),
    settlement(
        sid="volgograd",
        region="Волгоградская область",
        name="Волгоград",
    ),
    settlement(
        sid="saratov",
        region="Саратовская область",
        name="Саратов",
    ),
    settlement(
        sid="tolyatti",
        region="Самарская область",
        name="Тольятти",
    ),
    settlement(
        sid="izhevsk",
        region="Удмуртская Республика",
        name="Ижевск",
    ),
    settlement(
        sid="barnaul",
        region="Алтайский край",
        name="Барнаул",
    ),
    settlement(
        sid="ulyanovsk",
        region="Ульяновская область",
        name="Ульяновск",
    ),
    settlement(
        sid="irkutsk",
        region="Иркутская область",
        name="Иркутск",
    ),
    settlement(
        sid="khabarovsk",
        region="Хабаровский край",
        name="Хабаровск",
    ),
    settlement(
        sid="yaroslavl",
        region="Ярославская область",
        name="Ярославль",
    ),
    settlement(
        sid="makhachkala",
        region="Республика Дагестан",
        name="Махачкала",
    ),
    settlement(
        sid="orenburg",
        region="Оренбургская область",
        name="Оренбург",
    ),
    settlement(
        sid="novokuznetsk",
        region="Кемеровская область",
        name="Новокузнецк",
    ),
    settlement(
        sid="ryazan",
        region="Рязанская область",
        name="Рязань",
    ),
    settlement(
        sid="tomsk",
        region="Томская область",
        name="Томск",
    ),
    settlement(
        sid="astrakhan",
        region="Астраханская область",
        name="Астрахань",
    ),
    settlement(
        sid="penza",
        region="Пензенская область",
        name="Пенза",
    ),
    settlement(
        sid="lipetsk",
        region="Липецкая область",
        name="Липецк",
    ),
    settlement(
        sid="kirov",
        region="Кировская область",
        name="Киров",
    ),
    settlement(
        sid="cheboksary",
        region="Чувашская Республика",
        name="Чебоксары",
    ),
    settlement(
        sid="kaliningrad",
        region="Калининградская область",
        name="Калининград",
    ),
    settlement(
        sid="tula",
        region="Тульская область",
        name="Тула",
    ),
    settlement(
        sid="kursk",
        region="Курская область",
        name="Курск",
    ),
    settlement(
        sid="stavropol",
        region="Ставропольский край",
        name="Ставрополь",
    ),
    settlement(
        sid="ulan_ude",
        region="Республика Бурятия",
        name="Улан-Удэ",
    ),
    settlement(
        sid="kurgan",
        region="Курганская область",
        name="Курган",
    ),
    settlement(
        sid="vladimir",
        region="Владимирская область",
        name="Владимир",
    ),
    settlement(
        sid="kaluga",
        region="Калужская область",
        name="Калуга",
    ),
    settlement(
        sid="smolensk",
        region="Смоленская область",
        name="Смоленск",
    ),
    settlement(
        sid="bryansk",
        region="Брянская область",
        name="Брянск",
    ),
    settlement(
        sid="tver",
        region="Тверская область",
        name="Тверь",
    ),
    settlement(
        sid="arkhangelsk",
        region="Архангельская область",
        name="Архангельск",
    ),
    settlement(
        sid="murmansk",
        region="Мурманская область",
        name="Мурманск",
    ),
    settlement(
        sid="petrozavodsk",
        region="Республика Карелия",
        name="Петрозаводск",
    ),
    settlement(
        sid="syktyvkar",
        region="Республика Коми",
        name="Сыктывкар",
    ),
    settlement(
        sid="vologda",
        region="Вологодская область",
        name="Вологда",
    ),
    settlement(
        sid="cherepovets",
        region="Вологодская область",
        name="Череповец",
    ),
    settlement(
        sid="kostroma",
        region="Костромская область",
        name="Кострома",
    ),
    settlement(
        sid="ivanovo",
        region="Ивановская область",
        name="Иваново",
    ),
    settlement(
        sid="orel",
        region="Орловская область",
        name="Орёл",
    ),
    settlement(
        sid="belgorod",
        region="Белгородская область",
        name="Белгород",
    ),
    settlement(
        sid="tambov",
        region="Тамбовская область",
        name="Тамбов",
    ),
    settlement(
        sid="saransk",
        region="Республика Мордовия",
        name="Саранск",
    ),
    settlement(
        sid="yoshkar_ola",
        region="Республика Марий Эл",
        name="Йошкар-Ола",
    ),
    settlement(
        sid="naberezhnye_chelny",
        region="Республика Татарстан",
        name="Набережные Челны",
    ),
    settlement(
        sid="magnitogorsk",
        region="Челябинская область",
        name="Магнитогорск",
    ),
    settlement(
        sid="nizhny_tagil",
        region="Свердловская область",
        name="Нижний Тагил",
    ),
    settlement(
        sid="surgut",
        region="Ханты-Мансийский АО — Югра",
        name="Сургут",
    ),
    settlement(
        sid="khanty_mansiysk",
        region="Ханты-Мансийский АО — Югра",
        name="Ханты-Мансийск",
    ),
    settlement(
        sid="salekhard",
        region="Ямало-Ненецкий АО",
        name="Салехард",
    ),
    settlement(
        sid="novy_urengoy",
        region="Ямало-Ненецкий АО",
        name="Новый Уренгой",
    ),
    settlement(
        sid="noyabrsk",
        region="Ямало-Ненецкий АО",
        name="Ноябрьск",
    ),
    settlement(
        sid="kemerovo",
        region="Кемеровская область",
        name="Кемерово",
    ),
    settlement(
        sid="abakan",
        region="Республика Хакасия",
        name="Абакан",
    ),
    settlement(
        sid="kyzyl",
        region="Республика Тыва",
        name="Кызыл",
    ),
    settlement(
        sid="gorno_altaysk",
        region="Республика Алтай",
        name="Горно-Алтайск",
    ),
    settlement(
        sid="chita",
        region="Забайкальский край",
        name="Чита",
    ),
    settlement(
        sid="blagoveshchensk",
        region="Амурская область",
        name="Благовещенск",
    ),
    settlement(
        sid="birobidzhan",
        region="Еврейская автономная область",
        name="Биробиджан",
    ),
    settlement(
        sid="yuzhno_sakhalinsk",
        region="Сахалинская область",
        name="Южно-Сахалинск",
    ),
    settlement(
        sid="petropavlovsk_kamchatsky",
        region="Камчатский край",
        name="Петропавловск-Камчатский",
    ),
    settlement(
        sid="anadyr",
        region="Чукотский АО",
        name="Анадырь",
    ),
    settlement(
        sid="magadan",
        region="Магаданская область",
        name="Магадан",
    ),
    settlement(
        sid="nalchik",
        region="Кабардино-Балкарская Республика",
        name="Нальчик",
    ),
    settlement(
        sid="vladikavkaz",
        region="Республика Северная Осетия — Алания",
        name="Владикавказ",
    ),
    settlement(
        sid="cherkessk",
        region="Карачаево-Черкесская Республика",
        name="Черкесск",
    ),
    settlement(
        sid="grozny",
        region="Чеченская Республика",
        name="Грозный",
    ),
    settlement(
        sid="magas",
        region="Республика Ингушетия",
        name="Магас",
    ),
    settlement(
        sid="elista",
        region="Республика Калмыкия",
        name="Элиста",
    ),
    settlement(
        sid="maykop",
        region="Республика Адыгея",
        name="Майкоп",
    ),
    settlement(
        sid="sochi",
        region="Краснодарский край",
        name="Сочи",
    ),
    settlement(
        sid="anapa",
        region="Краснодарский край",
        name="Анапа",
    ),
    settlement(
        sid="novorossiysk",
        region="Краснодарский край",
        name="Новороссийск",
    ),
    settlement(
        sid="taganrog",
        region="Ростовская область",
        name="Таганрог",
    ),
    settlement(
        sid="nizhnevartovsk",
        region="Ханты-Мансийский АО — Югра",
        name="Нижневартовск",
    ),
    settlement(
        sid="bratsk",
        region="Иркутская область",
        name="Братск",
    ),
    settlement(
        sid="komsomolsk_on_amur",
        region="Хабаровский край",
        name="Комсомольск-на-Амуре",
    ),
    settlement(
        sid="ussuriysk",
        region="Приморский край",
        name="Уссурийск",
    ),
    settlement(
        sid="nakhodka",
        region="Приморский край",
        name="Находка",
    ),
    settlement(
        sid="berezniki",
        region="Пермский край",
        name="Березники",
    ),
    settlement(
        sid="zlatoust",
        region="Челябинская область",
        name="Златоуст",
    ),
    settlement(
        sid="miass",
        region="Челябинская область",
        name="Миасс",
    ),
    settlement(
        sid="kopeysk",
        region="Челябинская область",
        name="Копейск",
    ),
    settlement(
        sid="kamensk_uralsky",
        region="Свердловская область",
        name="Каменск-Уральский",
    ),
    settlement(
        sid="pervouralsk",
        region="Свердловская область",
        name="Первоуральск",
    ),
    settlement(
        sid="serov",
        region="Свердловская область",
        name="Серов",
    ),
    settlement(
        sid="nefteyugansk",
        region="Ханты-Мансийский АО — Югра",
        name="Нефтеюганск",
    ),
    settlement(
        sid="norilsk",
        region="Красноярский край",
        name="Норильск",
    ),
    settlement(
        sid="dudinka",
        region="Красноярский край",
        name="Дудинка",
    ),
    settlement(
        sid="achinsk",
        region="Красноярский край",
        name="Ачинск",
    ),
    settlement(
        sid="kansk",
        region="Красноярский край",
        name="Канск",
    ),
    settlement(
        sid="angarsk",
        region="Иркутская область",
        name="Ангарск",
    ),
    settlement(
        sid="ust_ilimsk",
        region="Иркутская область",
        name="Усть-Илимск",
    ),
    settlement(
        sid="severodvinsk",
        region="Архангельская область",
        name="Северодвинск",
    ),
    settlement(
        sid="naryan_mar",
        region="Ненецкий АО",
        name="Нарьян-Мар",
    ),
    settlement(
        sid="vorkuta",
        region="Республика Коми",
        name="Воркута",
    ),
    settlement(
        sid="ukhta",
        region="Республика Коми",
        name="Ухта",
    ),
    settlement(
        sid="pskov",
        region="Псковская область",
        name="Псков",
    ),
    settlement(
        sid="velikiy_novgorod",
        region="Новгородская область",
        name="Великий Новгород",
    ),
    settlement(
        sid="vyborg",
        region="Ленинградская область",
        name="Выборг",
    ),
    settlement(
        sid="gatchina",
        region="Ленинградская область",
        name="Гатчина",
    ),
    settlement(
        sid="podolsk",
        region="Московская область",
        name="Подольск",
    ),
    settlement(
        sid="khimki",
        region="Московская область",
        name="Химки",
    ),
    settlement(
        sid="balashikha",
        region="Московская область",
        name="Балашиха",
    ),
    settlement(
        sid="korolev",
        region="Московская область",
        name="Королёв",
    ),
    settlement(
        sid="mytishchi",
        region="Московская область",
        name="Мытищи",
    ),
    settlement(
        sid="lyubertsy",
        region="Московская область",
        name="Люберцы",
    ),
    settlement(
        sid="domodedovo",
        region="Московская область",
        name="Домодедово",
    ),
    settlement(
        sid="kolomna",
        region="Московская область",
        name="Коломна",
    ),
    settlement(
        sid="serpukhov",
        region="Московская область",
        name="Серпухов",
    ),
    settlement(
        sid="ramenskoye",
        region="Московская область",
        name="Раменское",
    ),
    settlement(
        sid="elektrostal",
        region="Московская область",
        name="Электросталь",
    ),
    settlement(
        sid="zhukovsky",
        region="Московская область",
        name="Жуковский",
    ),
    settlement(
        sid="krasnogorsk",
        region="Московская область",
        name="Красногорск",
    ),
    settlement(
        sid="reutov",
        region="Московская область",
        name="Реутов",
    ),
    settlement(
        sid="dolgoprudny",
        region="Московская область",
        name="Долгопрудный",
    ),
    settlement(
        sid="orekhovo_zuyevo",
        region="Московская область",
        name="Орехово-Зуево",
    ),
    settlement(
        sid="dmitrov",
        region="Московская область",
        name="Дмитров",
    ),
    settlement(
        sid="sergiev_posad",
        region="Московская область",
        name="Сергиев Посад",
    ),
    settlement(
        sid="naro_fominsk",
        region="Московская область",
        name="Наро-Фоминск",
    ),
    settlement(
        sid="zelenograd",
        region="г. Москва",
        name="Зеленоград",
    ),
    settlement(
        sid="apatity",
        region="Мурманская область",
        name="Апатиты",
    ),
    settlement(
        sid="kandalaksha",
        region="Мурманская область",
        name="Кандалакша",
    ),
    settlement(
        sid="monchegorsk",
        region="Мурманская область",
        name="Мончегорск",
    ),
    settlement(
        sid="severomorsk",
        region="Мурманская область",
        name="Североморск",
    ),
    settlement(
        sid="kostomuksha",
        region="Республика Карелия",
        name="Костомукша",
    ),
    settlement(
        sid="sortavala",
        region="Республика Карелия",
        name="Сортавала",
    ),
    settlement(
        sid="velikie_luki",
        region="Псковская область",
        name="Великие Луки",
    ),
    settlement(
        sid="tikhvin",
        region="Ленинградская область",
        name="Тихвин",
    ),
    settlement(
        sid="kingisepp",
        region="Ленинградская область",
        name="Кингисепп",
    ),
    settlement(
        sid="sosnovy_bor",
        region="Ленинградская область",
        name="Сосновый Бор",
    ),
    settlement(
        sid="vsevolozhsk",
        region="Ленинградская область",
        name="Всеволожск",
    ),
    settlement(
        sid="luga",
        region="Ленинградская область",
        name="Луга",
    ),
    settlement(
        sid="rybinsk",
        region="Ярославская область",
        name="Рыбинск",
    ),
    settlement(
        sid="pereslavl_zalessky",
        region="Ярославская область",
        name="Переславль-Залесский",
    ),
    settlement(
        sid="murom",
        region="Владимирская область",
        name="Муром",
    ),
    settlement(
        sid="kovrov",
        region="Владимирская область",
        name="Ковров",
    ),
    settlement(
        sid="aleksandrov",
        region="Владимирская область",
        name="Александров",
    ),
    settlement(
        sid="vyazma",
        region="Смоленская область",
        name="Вязьма",
    ),
    settlement(
        sid="staraya_russa",
        region="Новгородская область",
        name="Старая Русса",
    ),
    settlement(
        sid="borovichi",
        region="Новгородская область",
        name="Боровичи",
    ),
    settlement(
        sid="ust_kut",
        region="Иркутская область",
        name="Усть-Кут",
    ),
    settlement(
        sid="severobaykalsk",
        region="Республика Бурятия",
        name="Северобайкальск",
    ),
    settlement(
        sid="tynda",
        region="Амурская область",
        name="Тында",
    ),
    settlement(
        sid="neryungri",
        region="Республика Саха (Якутия)",
        name="Нерюнгри",
    ),
    settlement(
        sid="mirny",
        region="Республика Саха (Якутия)",
        name="Мирный",
    ),
    settlement(
        sid="lensk",
        region="Республика Саха (Якутия)",
        name="Ленск",
    ),
    settlement(
        sid="aldan",
        region="Республика Саха (Якутия)",
        name="Алдан",
    ),
    settlement(
        sid="susuman",
        region="Магаданская область",
        name="Сусуман",
    ),
    settlement(
        sid="bilibino",
        region="Чукотский АО",
        name="Билибино",
    ),
    settlement(
        sid="pevek",
        region="Чукотский АО",
        name="Певек",
    ),
    settlement(
        sid="ust_kamchatsk",
        region="Камчатский край",
        name="Усть-Камчатск",
        settlement_type="посёлок",
    ),
    settlement(
        sid="okhotsk",
        region="Хабаровский край",
        name="Охотск",
        settlement_type="посёлок",
    ),
    settlement(
        sid="vanino",
        region="Хабаровский край",
        name="Ванино",
        settlement_type="посёлок",
    ),
    settlement(
        sid="sovetskaya_gavan",
        region="Хабаровский край",
        name="Советская Гавань",
    ),
    settlement(
        sid="amursk",
        region="Хабаровский край",
        name="Амурск",
    ),
    settlement(
        sid="nikolaevsk_on_amur",
        region="Хабаровский край",
        name="Николаевск-на-Амуре",
    ),
    settlement(
        sid="okha",
        region="Сахалинская область",
        name="Оха",
    ),
    settlement(
        sid="korsakov",
        region="Сахалинская область",
        name="Корсаков",
    ),
    settlement(
        sid="kholmsk",
        region="Сахалинская область",
        name="Холмск",
    ),
    settlement(
        sid="severo_kurilsk",
        region="Сахалинская область",
        name="Северо-Курильск",
    ),
    settlement(
        sid="yuzhno_kurilsk",
        region="Сахалинская область",
        name="Южно-Курильск",
        settlement_type="посёлок",
    ),
    settlement(
        sid="dalnegorsk",
        region="Приморский край",
        name="Дальнегорск",
    ),
    settlement(
        sid="dalnerechensk",
        region="Приморский край",
        name="Дальнереченск",
    ),
    settlement(
        sid="arsenyev",
        region="Приморский край",
        name="Арсеньев",
    ),
    settlement(
        sid="spassk_dalny",
        region="Приморский край",
        name="Спасск-Дальний",
    ),
    settlement(
        sid="partizansk",
        region="Приморский край",
        name="Партизанск",
    ),
    settlement(
        sid="lesozavodsk",
        region="Приморский край",
        name="Лесозаводск",
    ),
    settlement(
        sid="bolshoy_kamen",
        region="Приморский край",
        name="Большой Камень",
    ),
    settlement(
        sid="artyom",
        region="Приморский край",
        name="Артём",
    ),
    settlement(
        sid="zheleznogorsk_krasnoyarsky",
        region="Красноярский край",
        name="Железногорск",
    ),
    settlement(
        sid="zelenogorsk_krasnoyarsky",
        region="Красноярский край",
        name="Зеленогорск",
    ),
    settlement(
        sid="minusinsk",
        region="Красноярский край",
        name="Минусинск",
    ),
    settlement(
        sid="lesosibirsk",
        region="Красноярский край",
        name="Лесосибирск",
    ),
    settlement(
        sid="igarka",
        region="Красноярский край",
        name="Игарка",
    ),
    settlement(
        sid="khatanga",
        region="Красноярский край",
        name="Хатанга",
        settlement_type="посёлок",
    ),
    settlement(
        sid="dikson",
        region="Красноярский край",
        name="Диксон",
        settlement_type="посёлок",
    ),
    settlement(
        sid="tiksi",
        region="Республика Саха (Якутия)",
        name="Тикси",
        settlement_type="посёлок",
    ),
    settlement(
        sid="verkhoyansk",
        region="Республика Саха (Якутия)",
        name="Верхоянск",
    ),
    settlement(
        sid="oymyakon",
        region="Республика Саха (Якутия)",
        name="Оймякон",
        settlement_type="село",
    ),
    settlement(
        sid="kogalym",
        region="Ханты-Мансийский АО — Югра",
        name="Когалым",
    ),
    settlement(
        sid="urai",
        region="Ханты-Мансийский АО — Югра",
        name="Урай",
    ),
    settlement(
        sid="nyagan",
        region="Ханты-Мансийский АО — Югра",
        name="Нягань",
    ),
    settlement(
        sid="nadym",
        region="Ямало-Ненецкий АО",
        name="Надым",
    ),
    settlement(
        sid="muravlenko",
        region="Ямало-Ненецкий АО",
        name="Муравленко",
    ),
    settlement(
        sid="gubkinsky",
        region="Ямало-Ненецкий АО",
        name="Губкинский",
    ),
    settlement(
        sid="labytnangi",
        region="Ямало-Ненецкий АО",
        name="Лабытнанги",
    ),
    settlement(
        sid="yamburg",
        region="Ямало-Ненецкий АО",
        name="Ямбург",
        settlement_type="посёлок",
    ),
]


# ---------------------------------------------------------------------------
# Merge с данными, собранными парсером ese.pro (см. scripts/scrape_ese.py).
# ---------------------------------------------------------------------------

ESE_DATA_PATH = ROOT / "outputs" / "ese-data.json"

SOURCE_SP131 = "СП 131.13330; сверено через ese.pro/tools/calculatory/klimaticheskie-nagruzki/"
SOURCE_FROST = "СП 22.13330; сверено через ese.pro/tools/calculatory/klimaticheskie-nagruzki/"


def _round_sg(kpa: float | None) -> float | None:
    """Округлить уточнённое значение Sg из ese.pro до района СП 20 (0.5..4.0)."""
    if kpa is None:
        return None
    # ese.pro показывает уточнённое Sg (например 1.45 для Москвы).
    # Для совместимости с SNOW_REGION_TO_SG_KPA храним округлённое значение
    # района (1.5 для III), но точное оставляем в комментарии.
    snow_region_to_sg = {0.5: 0.5, 1.0: 1.0, 1.5: 1.5, 2.0: 2.0, 2.5: 2.5, 3.0: 3.0, 3.5: 3.5, 4.0: 4.0}
    # round up to nearest district
    for v in sorted(snow_region_to_sg):
        if kpa <= v + 0.001:
            return v
    return 4.0


def merge_ese_data() -> None:
    """Обогатить DATA значениями из outputs/ese-data.json (если файл есть)."""
    if not ESE_DATA_PATH.exists():
        print(f"[merge] {ESE_DATA_PATH} not found — skipping merge")
        return

    with ESE_DATA_PATH.open("r", encoding="utf-8") as f:
        ese_state = json.load(f)

    enriched = 0
    for s in DATA:
        sid = s["id"]
        row = ese_state.get(sid)
        if not row or not row.get("data"):
            continue
        d = row["data"]

        # ── snow ──────────────────────────────────────────────────────────────
        snow = d.get("loads", {}).get("snow", {})
        if snow.get("region") and snow.get("kpa") is not None:
            sg_district = _round_sg(snow["kpa"])
            s["snow"] = {
                "region": snow["region"],
                "sgKpa": sg_district,
                "source": SOURCE_ESE_PRO,
                "status": "verified",
            }
            # сохранить уточнённое значение в комментарий, если отличается
            if abs(snow["kpa"] - (sg_district or 0)) > 0.01:
                exact = snow["kpa"]
                base = s.get("comment") or ""
                if "уточнённое" not in base and "уточнен" not in base:
                    tag = f"Sg уточнённое ese.pro: {exact} кПа"
                    s["comment"] = (base + " " + tag).strip()

        # ── wind ──────────────────────────────────────────────────────────────
        wind = d.get("loads", {}).get("wind", {})
        if wind.get("region") and wind.get("kpa") is not None:
            s["wind"] = {
                "region": wind["region"],
                "w0Kpa": wind["kpa"],
                "source": SOURCE_ESE_PRO,
                "status": "verified",
            }

        # ── ice ───────────────────────────────────────────────────────────────
        ice = d.get("loads", {}).get("ice", {})
        if ice.get("region") and ice.get("mm") is not None:
            s["ice"] = {
                "region": ice["region"],
                "iceThicknessMm": ice["mm"],
                "source": SOURCE_ESE_PRO,
                "status": "verified",
            }

        # ── seismic ──────────────────────────────────────────────────────────
        seismic = d.get("seismic", {})
        if seismic.get("mapA") is not None:
            # Для записи в seismic.points используем карту А (массовое строительство).
            s["seismic"] = {
                "points": seismic["mapA"],
                "source": SOURCE_ESE_PRO,
                "status": "verified",
            }

        # ── frost depth ──────────────────────────────────────────────────────
        frost = d.get("frostDepth", {})
        if any(frost.get(k) is not None for k in ("loamy", "sandyFine", "sandyCoarse", "coarseFragmental")):
            s["frostDepth"] = {
                "loamy": frost.get("loamy"),
                "sandyFine": frost.get("sandyFine"),
                "sandyCoarse": frost.get("sandyCoarse"),
                "coarseFragmental": frost.get("coarseFragmental"),
                "source": SOURCE_FROST,
                "status": "verified",
            }

        # ── cold period (СП 131) ────────────────────────────────────────────
        cold = d.get("cold", {})
        if cold:
            s["coldPeriod"] = {
                "tempColdestDay098": cold.get("tempColdestDay098"),
                "tempColdestDay092": cold.get("tempColdestDay092"),
                "tempColdest5days098": cold.get("tempColdest5days098"),
                "tempColdest5days092": cold.get("tempColdest5days092"),
                "temp094": cold.get("temp094"),
                "absMin": cold.get("absMin"),
                "dailyAmplitude": cold.get("dailyAmplitude"),
                "durationLe0": cold.get("durationLe0"),
                "meanLe0": cold.get("meanLe0"),
                "durationLe8": cold.get("durationLe8"),
                "meanLe8": cold.get("meanLe8"),
                "durationLe10": cold.get("durationLe10"),
                "meanLe10": cold.get("meanLe10"),
                "humidityCold": cold.get("humidityCold"),
                "humidityCold15": cold.get("humidityCold15"),
                "precipNovMar": cold.get("precipNovMar"),
                "prevailingWindDecFeb": cold.get("prevailingWindDecFeb"),
                "maxWindJan": cold.get("maxWindJan"),
                "meanWindLe8": cold.get("meanWindLe8"),
                "source": SOURCE_SP131,
                "status": "verified",
            }

        # ── warm period (СП 131) ────────────────────────────────────────────
        warm = d.get("warm", {})
        if warm:
            s["warmPeriod"] = {
                "barometric": warm.get("barometric"),
                "temp095": warm.get("temp095"),
                "temp099": warm.get("temp099"),
                "meanMaxTempWarmMonth": warm.get("meanMaxTempWarmMonth"),
                "absMax": warm.get("absMax"),
                "dailyAmplitude": warm.get("dailyAmplitude"),
                "humidityWarm": warm.get("humidityWarm"),
                "humidityWarm15": warm.get("humidityWarm15"),
                "precipAprOct": warm.get("precipAprOct"),
                "dailyMaxPrecip": warm.get("dailyMaxPrecip"),
                "prevailingWindJunAug": warm.get("prevailingWindJunAug"),
                "minWindJul": warm.get("minWindJul"),
                "source": SOURCE_SP131,
                "status": "verified",
            }

        # ── monthly temps ───────────────────────────────────────────────────
        mt = d.get("monthlyTemps")
        if mt and len(mt) == 13:
            s["monthlyTemps"] = {
                "byMonth": [float(x) if x is not None else None for x in mt[:12]],
                "yearly": float(mt[12]) if mt[12] is not None else None,
                "source": SOURCE_SP131,
                "status": "verified",
            }

        # ── обновление сводного статуса ─────────────────────────────────────
        params = [s["snow"]["status"], s["wind"]["status"], s["ice"]["status"], s["seismic"]["status"]]
        if all(p == "verified" for p in params):
            s["dataStatus"] = "verified"
        elif any(p == "verified" for p in params):
            s["dataStatus"] = "partial"
        # else: оставить как было

        enriched += 1

    print(f"[merge] обогащено {enriched}/{len(DATA)} записей из ese.pro")


def write_json() -> None:
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(DATA, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="2F5597")
HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)


def style_header_row(ws, row: int = 1) -> None:
    for cell in ws[row]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGN
    ws.freeze_panes = ws[f"A{row + 1}"]


def autosize(ws, min_width: int = 10, max_width: int = 40) -> None:
    for col_idx, col_cells in enumerate(ws.columns, start=1):
        length = min_width
        for cell in col_cells:
            v = cell.value
            if v is None:
                continue
            length = max(length, min(max_width, len(str(v)) + 2))
        ws.column_dimensions[get_column_letter(col_idx)].width = length


MASTER_HEADERS = [
    "id",
    "country",
    "region",
    "settlement",
    "settlement_type",
    "snow_region",
    "sg_kpa",
    "snow_source",
    "snow_status",
    "wind_region",
    "w0_kpa",
    "wind_source",
    "wind_status",
    "ice_region",
    "ice_thickness_mm",
    "ice_source",
    "ice_status",
    "seismic_points",
    "seismic_source",
    "seismic_status",
    "terrain_type_default",
    "terrain_type_allowed",
    "manual_allowed",
    "expert_override_allowed",
    "data_status",
    "comment",
]

CONTROL_CITIES = [
    "Москва",
    "Санкт-Петербург",
    "Челябинск",
    "Екатеринбург",
    "Казань",
    "Новосибирск",
    "Краснодар",
    "Пермь",
    "Уфа",
    "Самара",
    "Ростов-на-Дону",
    "Тюмень",
    "Омск",
    "Владивосток",
    "Якутск",
]


def row_for_settlement(s: dict[str, Any]) -> list[Any]:
    return [
        s["id"],
        s["country"],
        s["region"],
        s["settlement"],
        s["settlementType"],
        s["snow"]["region"],
        s["snow"]["sgKpa"],
        s["snow"]["source"],
        s["snow"]["status"],
        s["wind"]["region"],
        s["wind"]["w0Kpa"],
        s["wind"]["source"],
        s["wind"]["status"],
        s["ice"]["region"],
        s["ice"]["iceThicknessMm"],
        s["ice"]["source"],
        s["ice"]["status"],
        s["seismic"]["points"],
        s["seismic"]["source"],
        s["seismic"]["status"],
        s["terrain"]["defaultType"],
        ", ".join(s["terrain"]["allowedTypes"]),
        s["manualAllowed"],
        s["expertOverrideAllowed"],
        s["dataStatus"],
        s["comment"],
    ]


def write_xlsx() -> None:
    XLSX_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    # 1. 01_master_settlements -------------------------------------------------
    ws_master = wb.active
    ws_master.title = "01_master_settlements"
    ws_master.append(MASTER_HEADERS)
    for s in DATA:
        ws_master.append(row_for_settlement(s))
    style_header_row(ws_master)
    autosize(ws_master)

    # 2. 02_value_maps ---------------------------------------------------------
    ws_maps = wb.create_sheet("02_value_maps")
    ws_maps.append(["Тип справочника", "Код", "Значение", "Единицы", "Описание"])
    snow_map = [
        ("I", 0.5),
        ("II", 1.0),
        ("III", 1.5),
        ("IV", 2.0),
        ("V", 2.5),
        ("VI", 3.0),
        ("VII", 3.5),
        ("VIII", 4.0),
    ]
    for code, val in snow_map:
        ws_maps.append(
            [
                "Снеговой район (Sg)",
                code,
                val,
                "кПа",
                "Нормативное значение веса снегового покрова",
            ]
        )
    wind_map = [
        ("Ia", 0.17),
        ("I", 0.23),
        ("II", 0.30),
        ("III", 0.38),
        ("IV", 0.48),
        ("V", 0.60),
        ("VI", 0.73),
        ("VII", 0.85),
    ]
    for code, val in wind_map:
        ws_maps.append(
            [
                "Ветровой район (w0)",
                code,
                val,
                "кПа",
                "Нормативное значение ветрового давления",
            ]
        )
    terrain_map = [
        ("A", "открытая местность"),
        ("B", "городская / лесная местность"),
        ("C", "плотная городская застройка"),
    ]
    for code, descr in terrain_map:
        ws_maps.append(["Тип местности", code, "", "", descr])
    style_header_row(ws_maps)
    autosize(ws_maps)

    # 3. 03_control_checks -----------------------------------------------------
    ws_control = wb.create_sheet("03_control_checks")
    ws_control.append(
        [
            "settlement",
            "id",
            "snow_region",
            "sg_kpa",
            "wind_region",
            "w0_kpa",
            "ice_region",
            "ice_thickness_mm",
            "seismic_points",
            "data_status",
            "comment",
        ]
    )
    by_name = {s["settlement"]: s for s in DATA}
    for name in CONTROL_CITIES:
        s = by_name.get(name)
        if s is None:
            ws_control.append([name, "", "", "", "", "", "", "", "", "", "не найден"])
            continue
        ws_control.append(
            [
                s["settlement"],
                s["id"],
                s["snow"]["region"],
                s["snow"]["sgKpa"],
                s["wind"]["region"],
                s["wind"]["w0Kpa"],
                s["ice"]["region"],
                s["ice"]["iceThicknessMm"],
                s["seismic"]["points"],
                s["dataStatus"],
                s["comment"],
            ]
        )
    style_header_row(ws_control)
    autosize(ws_control)

    # 4a. 05_climate_extras ----------------------------------------------------
    ws_extras = wb.create_sheet("05_climate_extras")
    extras_headers = [
        "id",
        "settlement",
        "region",
        # frost depth (нормативная dfn, м)
        "frost_loamy",
        "frost_sandy_fine",
        "frost_sandy_coarse",
        "frost_coarse_fragm",
        # cold period (СП 131.13330)
        "t_coldest_day_098",
        "t_coldest_day_092",
        "t_coldest_5days_098",
        "t_coldest_5days_092",
        "t_094",
        "t_abs_min",
        "amp_cold_month",
        "dur_le0",
        "mean_le0",
        "dur_le8",
        "mean_le8",
        "dur_le10",
        "mean_le10",
        "humidity_cold",
        "humidity_cold_15",
        "precip_nov_mar",
        "wind_dir_dec_feb",
        "max_wind_jan",
        "mean_wind_le8",
        # warm period
        "barometric_hpa",
        "t_095",
        "t_099",
        "mean_max_t_warm",
        "t_abs_max",
        "amp_warm_month",
        "humidity_warm",
        "humidity_warm_15",
        "precip_apr_oct",
        "daily_max_precip",
        "wind_dir_jun_aug",
        "min_wind_jul",
        # monthly temps
        "t_jan",
        "t_feb",
        "t_mar",
        "t_apr",
        "t_may",
        "t_jun",
        "t_jul",
        "t_aug",
        "t_sep",
        "t_oct",
        "t_nov",
        "t_dec",
        "t_year",
    ]
    ws_extras.append(extras_headers)
    for s in DATA:
        fd = s.get("frostDepth") or {}
        cp = s.get("coldPeriod") or {}
        wp = s.get("warmPeriod") or {}
        mt = s.get("monthlyTemps") or {}
        by_month = (mt.get("byMonth") or [None] * 12) if mt else [None] * 12
        ws_extras.append(
            [
                s["id"], s["settlement"], s["region"],
                fd.get("loamy"), fd.get("sandyFine"), fd.get("sandyCoarse"), fd.get("coarseFragmental"),
                cp.get("tempColdestDay098"), cp.get("tempColdestDay092"),
                cp.get("tempColdest5days098"), cp.get("tempColdest5days092"),
                cp.get("temp094"), cp.get("absMin"),
                cp.get("dailyAmplitude"),
                cp.get("durationLe0"), cp.get("meanLe0"),
                cp.get("durationLe8"), cp.get("meanLe8"),
                cp.get("durationLe10"), cp.get("meanLe10"),
                cp.get("humidityCold"), cp.get("humidityCold15"),
                cp.get("precipNovMar"),
                cp.get("prevailingWindDecFeb"),
                cp.get("maxWindJan"), cp.get("meanWindLe8"),
                wp.get("barometric"),
                wp.get("temp095"), wp.get("temp099"),
                wp.get("meanMaxTempWarmMonth"), wp.get("absMax"),
                wp.get("dailyAmplitude"),
                wp.get("humidityWarm"), wp.get("humidityWarm15"),
                wp.get("precipAprOct"), wp.get("dailyMaxPrecip"),
                wp.get("prevailingWindJunAug"), wp.get("minWindJul"),
                *by_month, mt.get("yearly"),
            ]
        )
    style_header_row(ws_extras)
    autosize(ws_extras)

    # 4. 04_sources_plan -------------------------------------------------------
    ws_sources = wb.create_sheet("04_sources_plan")
    ws_sources.append(["Источник", "Назначение", "Статус"])
    sources = [
        (
            "СП 20.13330.2016, приложение К",
            "Sg по населённым пунктам",
            "основной источник",
        ),
        (
            "СП 20.13330.2016",
            "Карты снегового, ветрового и гололёдного районирования",
            "основной источник",
        ),
        ("СП 14.13330", "Сейсмичность (карты А/B/C ОСР-2015)", "основной источник"),
        (
            "СП 131.13330",
            "Климатические параметры холодного и тёплого периодов, среднемесячные T",
            "основной источник",
        ),
        (
            "СП 22.13330",
            "Глубина сезонного промерзания грунтов (нормативная dfn)",
            "основной источник",
        ),
        (
            "ese.pro/tools/calculatory/klimaticheskie-nagruzki/",
            "Сводный калькулятор СП 14/20/131 + СП 22 (агрегатор)",
            "сверочный источник",
        ),
    ]
    for row in sources:
        ws_sources.append(row)
    style_header_row(ws_sources)
    autosize(ws_sources)

    wb.save(XLSX_PATH)


def main() -> None:
    merge_ese_data()
    write_json()
    write_xlsx()
    print(f"settlements: {len(DATA)}")
    print(f"json:  {JSON_PATH}")
    print(f"xlsx:  {XLSX_PATH}")


if __name__ == "__main__":
    main()
