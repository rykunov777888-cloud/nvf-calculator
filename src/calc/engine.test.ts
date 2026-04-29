import { describe, expect, it } from "vitest";
import { runCalculation } from "./engine";
import { terrainFactor, aerodynamicCoefficient } from "./terrain";
import type { CalculationInput } from "./types";

describe("terrainFactor по СП 20.13330.2016, формула 11.3", () => {
  it("тип A на 10 м даёт k = 1.0", () => {
    expect(terrainFactor("A", 10)).toBeCloseTo(1.0, 3);
  });

  it("тип B на 10 м даёт k = 0.65", () => {
    expect(terrainFactor("B", 10)).toBeCloseTo(0.65, 3);
  });

  it("тип C на 10 м даёт k = 0.40", () => {
    expect(terrainFactor("C", 10)).toBeCloseTo(0.4, 3);
  });

  it("тип A на 20 м даёт k ≈ 1.23 (формула k = 1.0·(20/10)^0.3)", () => {
    expect(terrainFactor("A", 20)).toBeCloseTo(
      1.0 * Math.pow(20 / 10, 0.3),
      3,
    );
  });

  it("тип A на 2 м использует z_min = 5", () => {
    expect(terrainFactor("A", 2)).toBeCloseTo(terrainFactor("A", 5), 3);
  });
});

describe("aerodynamicCoefficient", () => {
  it("в поле фасада даёт c = 1.2", () => {
    expect(aerodynamicCoefficient("field")).toBe(1.2);
  });
  it("на краю даёт c = 1.6", () => {
    expect(aerodynamicCoefficient("edge")).toBe(1.6);
  });
  it("в углу даёт c = 2.0", () => {
    expect(aerodynamicCoefficient("corner")).toBe(2.0);
  });
});

const MOSCOW_INPUT: CalculationInput = {
  settlementId: "moscow",
  terrainType: "B",
  heightM: 20,
  windZone: "field",
  bracketPitchMm: 1000,
  profilePitchMm: 600,
  loadCase: "summer",
  profileId: "g_40x40x1.2_zn",
  bracketId: "kk_150_zn",
};

describe("runCalculation для Москвы, высота 20 м, тип B, поле фасада", () => {
  const result = runCalculation(MOSCOW_INPUT);

  it("возвращает w0 = 0.23 кПа (Москва — I ветровой район)", () => {
    expect(result.loads.w0Kpa).toBeCloseTo(0.23, 2);
  });

  it("коэффициент k(z) для B на 20 м", () => {
    // k = 0.65 · (20/10)^(2·0.20) = 0.65 · 2^0.4 ≈ 0.858
    expect(result.loads.kZ).toBeCloseTo(0.65 * Math.pow(2, 0.4), 3);
  });

  it("аэродинамический коэффициент c = 1.2 (field)", () => {
    expect(result.loads.c).toBe(1.2);
  });

  it("γ_f = 1.4", () => {
    expect(result.loads.gammaF).toBe(1.4);
  });

  it("пиковое давление wPeak > 0", () => {
    expect(result.loads.wPeakPa).toBeGreaterThan(0);
  });

  it("линейная нагрузка на профиль положительна", () => {
    expect(result.loads.qProfileNmm).toBeGreaterThan(0);
  });

  it("сила на кронштейн положительна", () => {
    expect(result.loads.fBracketN).toBeGreaterThan(0);
  });

  it("профиль даёт 2 проверки", () => {
    expect(result.profile.checks).toHaveLength(2);
  });

  it("кронштейн даёт 3 проверки", () => {
    expect(result.bracket.checks).toHaveLength(3);
  });

  it("содержит предупреждения про условные характеристики", () => {
    expect(result.warnings.length).toBeGreaterThan(0);
  });
});

describe("runCalculation edge cases", () => {
  it("кидает ошибку для неизвестного населённого пункта", () => {
    expect(() =>
      runCalculation({ ...MOSCOW_INPUT, settlementId: "unknown_xyz" }),
    ).toThrow(/не найден/);
  });

  it("кидает ошибку для неизвестного профиля", () => {
    expect(() =>
      runCalculation({ ...MOSCOW_INPUT, profileId: "unknown" }),
    ).toThrow(/Профиль/);
  });

  it("кидает ошибку для неизвестного кронштейна", () => {
    expect(() =>
      runCalculation({ ...MOSCOW_INPUT, bracketId: "unknown" }),
    ).toThrow(/Кронштейн/);
  });
});

describe("Эталонный ручной расчёт: Москва, тип B, z = 10 м, field", () => {
  const input: CalculationInput = {
    ...MOSCOW_INPUT,
    heightM: 10,
    bracketPitchMm: 1000,
    profilePitchMm: 600,
  };
  const r = runCalculation(input);

  it("k(10) для B = 0.65", () => {
    expect(r.loads.kZ).toBeCloseTo(0.65, 3);
  });

  it("wPeak = 1.4 · 230 · 0.65 · 1.2 = 251.16 Па", () => {
    // γf · w0[Pa] · k · c = 1.4 · 230 · 0.65 · 1.2 = 251.16
    const expected = 1.4 * 230 * 0.65 * 1.2;
    expect(r.loads.wPeakPa).toBeCloseTo(expected, 1);
  });

  it("q = w · B = 251.16 · 0.6 = 150.7 Н/м = 0.1507 Н/мм", () => {
    const expected = (1.4 * 230 * 0.65 * 1.2 * 600) / 1_000_000;
    expect(r.loads.qProfileNmm).toBeCloseTo(expected, 5);
  });

  it("F_кронш = w · A = 251.16 · 0.6 · 1.0 = 150.7 Н", () => {
    const expected = 1.4 * 230 * 0.65 * 1.2 * 0.6 * 1.0;
    expect(r.loads.fBracketN).toBeCloseTo(expected, 1);
  });

  it("момент на кронштейне M = F · 150 мм → σ = M/Wx", () => {
    const f = r.loads.fBracketN;
    const expectedSigma = (f * 150) / 1031; // МПа
    const bendingCheck = r.bracket.checks.find((c) =>
      c.name.includes("изгиб"),
    );
    expect(bendingCheck?.actual).toBeCloseTo(expectedSigma, 3);
  });
});
