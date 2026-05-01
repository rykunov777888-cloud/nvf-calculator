import type { TerrainType } from "./types";

const K_ZE_TABLE: Record<TerrainType, [number, number][]> = {
  A: [
    [5, 0.75], [10, 1.0], [20, 1.25], [40, 1.5], [60, 1.7],
    [80, 1.85], [100, 2.0], [150, 2.25], [200, 2.45], [250, 2.65],
    [300, 2.75], [350, 2.75],
  ],
  B: [
    [5, 0.5], [10, 0.65], [20, 0.85], [40, 1.1], [60, 1.3],
    [80, 1.45], [100, 1.6], [150, 1.9], [200, 2.1], [250, 2.3],
    [300, 2.5], [350, 2.5],
  ],
  C: [
    [5, 0.4], [10, 0.4], [20, 0.55], [40, 0.8], [60, 1.0],
    [80, 1.15], [100, 1.25], [150, 1.55], [200, 1.8], [250, 2.0],
    [300, 2.2], [350, 2.2],
  ],
};

const ZETA_TABLE: Record<TerrainType, [number, number][]> = {
  A: [
    [5, 0.85], [10, 0.76], [20, 0.69], [40, 0.62], [60, 0.58],
    [80, 0.56], [100, 0.54], [150, 0.51], [200, 0.49], [250, 0.47],
    [300, 0.46], [350, 0.46],
  ],
  B: [
    [5, 1.22], [10, 1.06], [20, 0.92], [40, 0.8], [60, 0.74],
    [80, 0.7], [100, 0.67], [150, 0.62], [200, 0.58], [250, 0.56],
    [300, 0.54], [350, 0.54],
  ],
  C: [
    [5, 1.78], [10, 1.78], [20, 1.5], [40, 1.26], [60, 1.14],
    [80, 1.06], [100, 1.0], [150, 0.9], [200, 0.84], [250, 0.8],
    [300, 0.76], [350, 0.76],
  ],
};

function interpolateTable(table: [number, number][], z: number): number {
  if (z <= table[0][0]) return table[0][1];
  if (z >= table[table.length - 1][0]) return table[table.length - 1][1];
  for (let i = 0; i < table.length - 1; i++) {
    if (z >= table[i][0] && z <= table[i + 1][0]) {
      const frac = (z - table[i][0]) / (table[i + 1][0] - table[i][0]);
      return table[i][1] + frac * (table[i + 1][1] - table[i][1]);
    }
  }
  return table[table.length - 1][1];
}

export function getKze(terrain: TerrainType, z_m: number): number {
  return interpolateTable(K_ZE_TABLE[terrain], Math.max(z_m, 5));
}

export function getZeta(terrain: TerrainType, z_m: number): number {
  return interpolateTable(ZETA_TABLE[terrain], Math.max(z_m, 5));
}

/** Table 11.6 of СП 20.13330 — spatial correlation ν(ρ, χ) */
const NU_RHO = [5, 10, 20, 40, 80, 160, 350];
const NU_CHI = [5, 10, 20, 40, 80, 100, 200];
const NU_DATA: number[][] = [
  [0.95, 0.92, 0.88, 0.83, 0.76, 0.73, 0.67],
  [0.89, 0.87, 0.83, 0.78, 0.71, 0.69, 0.63],
  [0.85, 0.83, 0.78, 0.73, 0.67, 0.65, 0.59],
  [0.80, 0.76, 0.72, 0.67, 0.62, 0.60, 0.55],
  [0.72, 0.67, 0.63, 0.59, 0.54, 0.52, 0.48],
  [0.67, 0.62, 0.58, 0.54, 0.50, 0.49, 0.45],
  [0.59, 0.56, 0.50, 0.47, 0.44, 0.42, 0.39],
];

function interpIdx(arr: number[], val: number): { lo: number; hi: number; frac: number } {
  if (val <= arr[0]) return { lo: 0, hi: 0, frac: 0 };
  for (let i = 0; i < arr.length - 1; i++) {
    if (val <= arr[i + 1]) {
      return { lo: i, hi: i + 1, frac: (val - arr[i]) / (arr[i + 1] - arr[i]) };
    }
  }
  const last = arr.length - 1;
  return { lo: last, hi: last, frac: 0 };
}

export function getNu(rho: number, chi: number): number {
  const ri = interpIdx(NU_RHO, rho);
  const ci = interpIdx(NU_CHI, chi);

  const v00 = NU_DATA[ri.lo][ci.lo];
  const v01 = NU_DATA[ri.lo][ci.hi];
  const v10 = NU_DATA[ri.hi][ci.lo];
  const v11 = NU_DATA[ri.hi][ci.hi];

  const top = v00 + ci.frac * (v01 - v00);
  const bot = v10 + ci.frac * (v11 - v10);
  return top + ri.frac * (bot - top);
}

function zoneTotal(
  w0: number,
  kze: number,
  cAero: number,
  gamma_f: number,
  zeta: number,
  nu: number,
): number {
  const mean = Math.abs(w0 * kze * cAero * gamma_f);
  const pulse = mean * zeta * nu;
  return mean + pulse;
}

export interface WindResult {
  /** B25: total horizontal for moment (max of long/short B-zone + FGH+) */
  horizontalPressure_kPa: number;
  /** C25: vertical roof component (FGH+ only) */
  verticalRoof_kPa: number;
}

/**
 * Wind calculation per СП 20.13330.2016 matching the Excel logic.
 *
 * B25 = max(long_B, short_B) + FGH+
 * C25 = FGH+
 */
export function calcWind(
  w0: number,
  terrain: TerrainType,
  height_m: number,
  span_m: number,
  length_m: number,
): WindResult {
  const h = Math.max(height_m, 5);
  const kze = getKze(terrain, h);
  const zeta = getZeta(terrain, h);
  const gamma_f = 1.4;

  // Correlation coefficients (nu) for different surfaces
  // Long side (wind on length_m facade):
  //   Windward A,B,C,FGH+: rho = 0.4*span, chi = height → nuY_long
  //   Leeward D,E: rho = length, chi = height → nuX_long
  const nuY_long = getNu(0.4 * span_m, h);

  // Short side (wind on span_m facade):
  //   Windward A,B: rho = span, chi = height → nuX_short (but actually uses nuY_short)
  const nuY_short = getNu(0.4 * length_m, h);

  // Zone B on long side (C = -0.8)
  const longB = zoneTotal(w0, kze, -0.8, gamma_f, zeta, nuY_long);
  // Zone B on short side (C = -0.8)
  const shortB = zoneTotal(w0, kze, -0.8, gamma_f, zeta, nuY_short);
  // FGH+ zone (C = 0.2)
  const fghPlus = zoneTotal(w0, kze, 0.2, gamma_f, zeta, nuY_long);

  return {
    horizontalPressure_kPa: Math.max(longB, shortB) + fghPlus,
    verticalRoof_kPa: fghPlus,
  };
}
