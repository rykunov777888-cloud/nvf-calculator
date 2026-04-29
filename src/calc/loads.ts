/**
 * Сбор нагрузок на НВФ по СП 20.13330.2016.
 *
 * Для MVP считаем только ветровую нагрузку — основной вид для ограждающих
 * конструкций фасада. Гололёдная нагрузка для вертикальных ограждений
 * незначительна и в MVP не учитывается (будет добавлена позже).
 */

import { getSettlementClimateById } from "../types/climate";
import { aerodynamicCoefficient, terrainFactor } from "./terrain";
import { GAMMA_F_WIND } from "./steel";
import type { CalculationInput, LoadsResult } from "./types";

export function calculateLoads(input: CalculationInput): LoadsResult {
  const climate = getSettlementClimateById(input.settlementId);
  if (!climate) {
    throw new Error(
      `Населённый пункт id="${input.settlementId}" не найден в справочнике.`,
    );
  }
  if (climate.wind.w0Kpa === null) {
    throw new Error(
      `Для населённого пункта "${climate.settlement}" не задано w0.`,
    );
  }

  const w0Kpa = climate.wind.w0Kpa;
  const kZ = terrainFactor(input.terrainType, input.heightM);
  const c = input.cAero ?? aerodynamicCoefficient(input.windZone);
  const gammaF = GAMMA_F_WIND;

  // Пиковое расчётное давление ветра (Па)
  const wPeakPa = gammaF * w0Kpa * 1000 * kZ * c;

  // Линейная нагрузка на профиль: q = w · B (грузовая полоса = шаг профилей)
  const qProfileNmm = (wPeakPa * input.profilePitchMm) / 1000 / 1000;
  // Н/мм² · мм = Н/мм; wPeakPa [Па = Н/м²] → [Н/мм²] делением на 10⁶

  // Сила на кронштейн: F = w · A_bracket
  // Площадь, обслуживаемая одним кронштейном =
  //   шаг кронштейнов по вертикали × шаг профилей по горизонтали (мм²)
  const aBracketM2 =
    (input.bracketPitchMm / 1000) * (input.profilePitchMm / 1000);
  const fBracketN = wPeakPa * aBracketM2;

  return { w0Kpa, kZ, c, gammaF, wPeakPa, qProfileNmm, fBracketN };
}
