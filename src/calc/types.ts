/**
 * Типы расчётного ядра для MVP калькулятора НВФ.
 */

import type { TerrainType } from "../types/climate";

/** Марка стали (СП 16.13330, табл. В.3 / В.5 — расчётные сопротивления). */
export interface SteelGrade {
  /** Название марки: 'S245' (С245), 'S255', 'S355', 'S500' и т.п. */
  name: string;
  /** Нормативное сопротивление Ryn (МПа). */
  ryn: number;
  /** Расчётное сопротивление Ry (МПа). */
  ry: number;
  /** Расчётное сопротивление Ru (МПа). */
  ru: number;
  /** Модуль упругости E (МПа). */
  e: number;
  /** Источник значений. */
  source: string;
}

/** Геометрические характеристики тонкостенного сечения относительно оси X-X. */
export interface SectionProperties {
  /** Площадь сечения, мм². */
  area: number;
  /** Момент инерции Ix, мм⁴. */
  ix: number;
  /** Момент сопротивления Wx, мм³. */
  wx: number;
  /** Радиус инерции ix, мм. */
  radiusX: number;
}

/** Справочник направляющих профилей подсистемы НВФ. */
export interface Profile {
  /** Идентификатор типа 'g_40x40x1.2_zn'. */
  id: string;
  /** Название 'Г-образный 40×40×1.2, оцинкованная сталь'. */
  name: string;
  /** Производитель. */
  manufacturer: string;
  /** Номинальное сечение / форма. */
  shape: "L" | "Z" | "hat" | "tube" | "other";
  /** Габаритные размеры (ширина × высота × толщина), мм. */
  sizeMm: { width: number; height: number; thickness: number };
  /** Марка стали. */
  steel: SteelGrade;
  /** Геометрические характеристики. */
  section: SectionProperties;
  /** Примечание / источник характеристик. */
  note: string;
}

/** Справочник кронштейнов подсистемы НВФ (консольные). */
export interface Bracket {
  /** Идентификатор типа 'kk_150_zn'. */
  id: string;
  /** Название 'КК, вылет 150 мм, оцинкованная сталь'. */
  name: string;
  /** Производитель. */
  manufacturer: string;
  /** Форма / тип. */
  shape: "KK" | "KKU" | "KR" | "other";
  /** Вылет (длина консоли), мм. */
  reachMm: number;
  /** Толщина стенки, мм. */
  thicknessMm: number;
  /** Ширина «спинки» кронштейна (по направлению профиля), мм. */
  webWidthMm: number;
  /** Высота полки («щёчек»), мм. */
  flangeHeightMm: number;
  /** Марка стали. */
  steel: SteelGrade;
  /** Характеристики сечения в опасном сечении (обычно у стены). */
  section: SectionProperties;
  /** Примечание / источник характеристик. */
  note: string;
}

/** Расчётные случаи. */
export type LoadCase = "summer" | "winter";

/** Зона ветрового давления на фасад. */
export type WindZone = "field" | "edge" | "corner";

/** Входные данные расчёта. */
export interface CalculationInput {
  /** Идентификатор населённого пункта (из settlements-climate.json). */
  settlementId: string;
  /** Тип местности по СП 20, табл. 11.2. */
  terrainType: TerrainType;
  /** Высота точки крепления над поверхностью земли z, м. */
  heightM: number;
  /** Зона ветрового давления (в поле / край / угол). */
  windZone: WindZone;
  /** Аэродинамический коэффициент c (если не задан — берётся по windZone). */
  cAero?: number;
  /** Шаг кронштейнов по вертикали (пролёт профиля), мм. */
  bracketPitchMm: number;
  /** Шаг профилей по горизонтали (грузовая полоса на профиль), мм. */
  profilePitchMm: number;
  /** Расчётный случай. */
  loadCase: LoadCase;
  /** Идентификатор профиля. */
  profileId: string;
  /** Идентификатор кронштейна. */
  bracketId: string;
}

/** Результат расчёта нагрузок. */
export interface LoadsResult {
  /** w0 по климатическим данным, кПа. */
  w0Kpa: number;
  /** Коэффициент k(z), безразмерный. */
  kZ: number;
  /** Аэродинамический коэффициент c, безразмерный. */
  c: number;
  /** Коэффициент надёжности по нагрузке γ_f. */
  gammaF: number;
  /** Пиковое расчётное давление ветра, Па. */
  wPeakPa: number;
  /** Линейная нагрузка на профиль, Н/мм. */
  qProfileNmm: number;
  /** Сосредоточенная сила на кронштейн, Н. */
  fBracketN: number;
}

/** Результат проверки элемента. */
export interface CheckResult {
  /** Название проверки. */
  name: string;
  /** Фактическое значение (например, напряжение). */
  actual: number;
  /** Предельно допустимое значение. */
  allowable: number;
  /** Единица измерения. */
  unit: string;
  /** Коэффициент загрузки (actual / allowable). */
  utilization: number;
  /** Прошла проверка или нет. */
  pass: boolean;
  /** Ссылка на пункт СП. */
  reference: string;
}

/** Результат расчёта одного элемента. */
export interface ElementResult {
  /** Идентификатор элемента. */
  elementId: string;
  /** Название элемента. */
  elementName: string;
  /** Проверки. */
  checks: CheckResult[];
  /** Общий вердикт. */
  pass: boolean;
  /** Максимальный коэффициент загрузки. */
  maxUtilization: number;
}

/** Полный результат расчёта. */
export interface CalculationResult {
  input: CalculationInput;
  loads: LoadsResult;
  profile: ElementResult;
  bracket: ElementResult;
  overallPass: boolean;
  warnings: string[];
}
