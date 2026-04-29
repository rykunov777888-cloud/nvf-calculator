/**
 * Проверка направляющего профиля подсистемы НВФ.
 *
 * Расчётная схема: однопролётная шарнирно опёртая балка длиной L (шаг
 * кронштейнов) под равномерно распределённой нагрузкой q (линейная
 * нагрузка от ветра на профиль).
 *
 *   Момент в пролёте: M = q·L² / 8
 *   Нормальное напряжение изгиба: σ = M / Wx
 *   Проверка прочности: σ ≤ Ry · γ_c
 *   Прогиб: f = 5·q·L⁴ / (384·E·Ix), допуск: f ≤ L/200
 */

import { GAMMA_C_SUBSYSTEM } from "./steel";
import type { CheckResult, ElementResult, LoadsResult, Profile } from "./types";

export function checkProfile(
  profile: Profile,
  loads: LoadsResult,
  bracketPitchMm: number,
): ElementResult {
  const { qProfileNmm } = loads;
  const L = bracketPitchMm;
  const { wx, ix } = profile.section;
  const { ry, e } = profile.steel;

  // Изгибающий момент и напряжение
  const momentNmm = (qProfileNmm * L * L) / 8;
  const sigmaMPa = momentNmm / wx; // Н/мм² = МПа
  const sigmaAllowMPa = ry * GAMMA_C_SUBSYSTEM;

  const strengthCheck: CheckResult = {
    name: "Прочность по нормальным напряжениям",
    actual: sigmaMPa,
    allowable: sigmaAllowMPa,
    unit: "МПа",
    utilization: sigmaMPa / sigmaAllowMPa,
    pass: sigmaMPa <= sigmaAllowMPa,
    reference: "СП 16.13330.2017, п. 8.2.1 (формула 41)",
  };

  // Прогиб: f = 5·q·L⁴ / (384·E·Ix)
  const deflectionMm = (5 * qProfileNmm * Math.pow(L, 4)) / (384 * e * ix);
  const deflectionAllowMm = L / 200;

  const deflectionCheck: CheckResult = {
    name: "Прогиб в пролёте",
    actual: deflectionMm,
    allowable: deflectionAllowMm,
    unit: "мм",
    utilization: deflectionMm / deflectionAllowMm,
    pass: deflectionMm <= deflectionAllowMm,
    reference: "СП 20.13330.2016, прилож. Д.2.1 (L/200)",
  };

  const checks = [strengthCheck, deflectionCheck];
  const maxUtilization = Math.max(...checks.map((c) => c.utilization));
  const pass = checks.every((c) => c.pass);

  return {
    elementId: profile.id,
    elementName: profile.name,
    checks,
    pass,
    maxUtilization,
  };
}
