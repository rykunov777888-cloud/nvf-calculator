/**
 * Проверка кронштейна подсистемы НВФ.
 *
 * Расчётная схема: жёстко защемлённая консоль длиной a (вылет) с
 * сосредоточенной силой F на свободном конце.
 *
 *   Изгибающий момент в основании: M = F · a
 *   Нормальное напряжение: σ = M / Wx
 *   Поперечная сила: V = F
 *   Касательное напряжение (среднее): τ = V / A_section
 *
 * Для MVP проверяем прочность по нормальным напряжениям и по касательным.
 * Проверка анкера в стене и проверка на смятие — отдельные задачи, в MVP
 * не учитываются.
 */

import { GAMMA_C_SUBSYSTEM } from "./steel";
import type {
  Bracket,
  CheckResult,
  ElementResult,
  LoadsResult,
} from "./types";

export function checkBracket(
  bracket: Bracket,
  loads: LoadsResult,
): ElementResult {
  const { fBracketN } = loads;
  const a = bracket.reachMm;
  const { wx, area } = bracket.section;
  const { ry, ru } = bracket.steel;

  // Изгиб
  const momentNmm = fBracketN * a;
  const sigmaMPa = momentNmm / wx;
  const sigmaAllowMPa = ry * GAMMA_C_SUBSYSTEM;

  const bendingCheck: CheckResult = {
    name: "Прочность кронштейна на изгиб (основание)",
    actual: sigmaMPa,
    allowable: sigmaAllowMPa,
    unit: "МПа",
    utilization: sigmaMPa / sigmaAllowMPa,
    pass: sigmaMPa <= sigmaAllowMPa,
    reference: "СП 16.13330.2017, п. 8.2.1 (формула 41)",
  };

  // Срез. Rs = 0.58 · Ry (приблизительно — СП 16 п. 8.2.2)
  const tauMPa = fBracketN / area;
  const rsMPa = 0.58 * ry;
  const tauAllowMPa = rsMPa * GAMMA_C_SUBSYSTEM;

  const shearCheck: CheckResult = {
    name: "Прочность кронштейна на срез",
    actual: tauMPa,
    allowable: tauAllowMPa,
    unit: "МПа",
    utilization: tauMPa / tauAllowMPa,
    pass: tauMPa <= tauAllowMPa,
    reference: "СП 16.13330.2017, п. 8.2.2",
  };

  // Смятие по пределу прочности (консервативная проверка, Ru)
  // Применяется в местах концентраторов (отверстия под анкер и т. п.).
  const ruCheck: CheckResult = {
    name: "Прочность в опасном сечении по Ru",
    actual: sigmaMPa,
    allowable: ru * GAMMA_C_SUBSYSTEM,
    unit: "МПа",
    utilization: sigmaMPa / (ru * GAMMA_C_SUBSYSTEM),
    pass: sigmaMPa <= ru * GAMMA_C_SUBSYSTEM,
    reference: "СП 16.13330.2017, п. 8.2.1 (формула 42)",
  };

  const checks = [bendingCheck, shearCheck, ruCheck];
  const maxUtilization = Math.max(...checks.map((c) => c.utilization));
  const pass = checks.every((c) => c.pass);

  return {
    elementId: bracket.id,
    elementName: bracket.name,
    checks,
    pass,
    maxUtilization,
  };
}
