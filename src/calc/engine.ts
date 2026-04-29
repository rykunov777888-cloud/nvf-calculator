/**
 * Точка входа расчётного ядра MVP.
 */

import { getBracketById } from "../data/brackets";
import { getProfileById } from "../data/profiles";
import { checkBracket } from "./bracket";
import { calculateLoads } from "./loads";
import { checkProfile } from "./profile";
import type { CalculationInput, CalculationResult } from "./types";

export function runCalculation(input: CalculationInput): CalculationResult {
  const profile = getProfileById(input.profileId);
  if (!profile) {
    throw new Error(`Профиль id="${input.profileId}" не найден.`);
  }
  const bracket = getBracketById(input.bracketId);
  if (!bracket) {
    throw new Error(`Кронштейн id="${input.bracketId}" не найден.`);
  }

  const loads = calculateLoads(input);
  const profileResult = checkProfile(profile, loads, input.bracketPitchMm);
  const bracketResult = checkBracket(bracket, loads);

  const warnings: string[] = [];
  if (input.loadCase === "winter") {
    warnings.push(
      "MVP: гололёдная нагрузка не учитывается; при фактическом проектировании " +
        "учитывать массу обледенения по СП 20.13330.2016, §12.",
    );
  }
  if (profile.section.wx === 518) {
    warnings.push(
      "Характеристики профиля условные (геометрический W_x без редукции). " +
        "Для проектирования использовать паспортные данные Металл Профиль.",
    );
  }
  if (bracket.section.wx === 1031) {
    warnings.push(
      "Характеристики кронштейна условные. Для проектирования " +
        "использовать паспортные данные Металл Профиль (КК / ККУ).",
    );
  }
  if (input.terrainType && input.heightM < 5 && input.terrainType === "A") {
    warnings.push(
      "Высота менее z_min = 5 м для типа местности A; в расчёте принята z = 5 м.",
    );
  }

  return {
    input,
    loads,
    profile: profileResult,
    bracket: bracketResult,
    overallPass: profileResult.pass && bracketResult.pass,
    warnings,
  };
}
