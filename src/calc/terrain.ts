/**
 * Коэффициент k(z_e) по СП 20.13330.2016, формула 11.3 и таблица 11.2.
 *
 * k(z_e) = k10 · (z_e / 10)^(2·α), z_e >= z_min
 *
 * Тип местности A: k10 = 1.00, α = 0.15, z_min =  5 м
 * Тип местности B: k10 = 0.65, α = 0.20, z_min = 10 м
 * Тип местности C: k10 = 0.40, α = 0.25, z_min = 10 м
 *
 * Значения z_min выбраны так, чтобы k(z_min) совпадало с табличными
 * якорными значениями (1.0 / 0.65 / 0.40 для z = 10 м).
 */

import type { TerrainType } from "../types/climate";

interface TerrainCoefficients {
  k10: number;
  alpha: number;
  zMin: number;
}

const TERRAIN_COEFFICIENTS: Record<TerrainType, TerrainCoefficients> = {
  A: { k10: 1.0, alpha: 0.15, zMin: 5 },
  B: { k10: 0.65, alpha: 0.2, zMin: 10 },
  C: { k10: 0.4, alpha: 0.25, zMin: 10 },
};

/** Вычислить k(z) для данного типа местности и высоты над поверхностью земли. */
export function terrainFactor(terrain: TerrainType, heightM: number): number {
  const { k10, alpha, zMin } = TERRAIN_COEFFICIENTS[terrain];
  const z = Math.max(heightM, zMin);
  return k10 * Math.pow(z / 10, 2 * alpha);
}

/** Аэродинамический коэффициент c для зоны фасада (СП 20, §11.1.7). */
export function aerodynamicCoefficient(
  zone: "field" | "edge" | "corner",
): number {
  // Значения приняты с учётом положительной и отрицательной компонент ветра.
  // Для элементов крепления панелей НВФ рекомендуется использовать
  // локальные значения c с учётом знакопеременной нагрузки.
  switch (zone) {
    case "field":
      return 1.2;
    case "edge":
      return 1.6;
    case "corner":
      return 2.0;
  }
}
