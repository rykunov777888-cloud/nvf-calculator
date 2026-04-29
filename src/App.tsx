import { useMemo, useState } from "react";
import { runCalculation } from "./calc/engine";
import type {
  CalculationInput,
  CalculationResult,
  LoadCase,
  WindZone,
} from "./calc/types";
import { BRACKETS } from "./data/brackets";
import { PROFILES } from "./data/profiles";
import {
  getSettlementClimateById,
  searchSettlements,
} from "./types/climate";
import type { TerrainType } from "./types/climate";

const TERRAIN_OPTIONS: { value: TerrainType; label: string }[] = [
  { value: "A", label: "A — открытая местность" },
  { value: "B", label: "B — городская / лесная" },
  { value: "C", label: "C — плотная городская застройка" },
];

const WIND_ZONE_OPTIONS: { value: WindZone; label: string }[] = [
  { value: "field", label: "В поле фасада (c = 1.2)" },
  { value: "edge", label: "Край / угол здания (c = 1.6)" },
  { value: "corner", label: "Угол / парапет (c = 2.0)" },
];

const LOAD_CASE_OPTIONS: { value: LoadCase; label: string }[] = [
  { value: "summer", label: "Лето (без гололёда)" },
  { value: "winter", label: "Зима (с гололёдом) — MVP: не учитывает массу льда" },
];

const DEFAULT_INPUT: CalculationInput = {
  settlementId: "moscow",
  terrainType: "B",
  heightM: 20,
  windZone: "field",
  bracketPitchMm: 1000,
  profilePitchMm: 600,
  loadCase: "summer",
  profileId: PROFILES[0].id,
  bracketId: BRACKETS[0].id,
};

export function App() {
  const [input, setInput] = useState<CalculationInput>(DEFAULT_INPUT);
  const [settlementQuery, setSettlementQuery] = useState("Москва");

  const settlementMatches = useMemo(() => {
    const q = settlementQuery.trim();
    if (q.length < 2) return [];
    return searchSettlements(q).slice(0, 8);
  }, [settlementQuery]);

  const selectedSettlement = getSettlementClimateById(input.settlementId);

  const [result, setResult] = useState<CalculationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = () => {
    setError(null);
    try {
      setResult(runCalculation(input));
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="app">
      <h1>Калькулятор НВФ — MVP</h1>
      <p className="subtitle">
        Статический расчёт направляющего профиля и кронштейна стальной
        подсистемы по СП 20.13330.2016 и СП 16.13330.2017. MVP с условными
        характеристиками элементов Металл Профиль.
      </p>

      <div className="panel">
        <h2>Исходные данные</h2>
        <div className="grid2">
          <div className="field">
            <label>Поиск города (начните вводить)</label>
            <input
              value={settlementQuery}
              onChange={(e) => setSettlementQuery(e.target.value)}
              placeholder="Напр. Москва"
            />
            {settlementMatches.length > 0 && (
              <select
                size={Math.min(settlementMatches.length, 6)}
                value={input.settlementId}
                onChange={(e) =>
                  setInput({ ...input, settlementId: e.target.value })
                }
              >
                {settlementMatches.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.settlement} ({s.region})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="field">
            <label>Выбранный город (по id)</label>
            <input
              value={
                selectedSettlement
                  ? `${selectedSettlement.settlement} — ${selectedSettlement.region}`
                  : input.settlementId
              }
              readOnly
            />
            {selectedSettlement && (
              <small>
                w₀ = {selectedSettlement.wind.w0Kpa ?? "—"} кПа (район{" "}
                {selectedSettlement.wind.region ?? "—"}), гололёд{" "}
                {selectedSettlement.ice.iceThicknessMm ?? "—"} мм, сейсмика{" "}
                {selectedSettlement.seismic.points ?? "—"} баллов
              </small>
            )}
          </div>

          <div className="field">
            <label>Тип местности</label>
            <select
              value={input.terrainType}
              onChange={(e) =>
                setInput({
                  ...input,
                  terrainType: e.target.value as TerrainType,
                })
              }
            >
              {TERRAIN_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Высота точки крепления z, м</label>
            <input
              type="number"
              min={1}
              max={500}
              step={1}
              value={input.heightM}
              onChange={(e) =>
                setInput({ ...input, heightM: Number(e.target.value) })
              }
            />
          </div>

          <div className="field">
            <label>Зона фасада (аэродинамический коэффициент)</label>
            <select
              value={input.windZone}
              onChange={(e) =>
                setInput({ ...input, windZone: e.target.value as WindZone })
              }
            >
              {WIND_ZONE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Расчётный случай</label>
            <select
              value={input.loadCase}
              onChange={(e) =>
                setInput({ ...input, loadCase: e.target.value as LoadCase })
              }
            >
              {LOAD_CASE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Шаг кронштейнов по вертикали (пролёт профиля), мм</label>
            <input
              type="number"
              min={100}
              max={3000}
              step={50}
              value={input.bracketPitchMm}
              onChange={(e) =>
                setInput({ ...input, bracketPitchMm: Number(e.target.value) })
              }
            />
          </div>

          <div className="field">
            <label>Шаг профилей по горизонтали, мм</label>
            <input
              type="number"
              min={100}
              max={3000}
              step={50}
              value={input.profilePitchMm}
              onChange={(e) =>
                setInput({ ...input, profilePitchMm: Number(e.target.value) })
              }
            />
          </div>

          <div className="field">
            <label>Профиль</label>
            <select
              value={input.profileId}
              onChange={(e) =>
                setInput({ ...input, profileId: e.target.value })
              }
            >
              {PROFILES.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Кронштейн</label>
            <select
              value={input.bracketId}
              onChange={(e) =>
                setInput({ ...input, bracketId: e.target.value })
              }
            >
              {BRACKETS.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="actions">
          <button className="primary" onClick={handleRun}>
            Рассчитать
          </button>
        </div>

        {error && (
          <div className="warn-list" role="alert" style={{ marginTop: 16 }}>
            <b>Ошибка расчёта:</b> {error}
          </div>
        )}
      </div>

      {result && <ResultPanel result={result} />}

      <footer>
        Данные города — из{" "}
        <code>src/data/regions/settlements-climate.json</code> (205 городов,
        сверено через ese.pro, см. PR #1). Расчёт по СП 20.13330.2016
        (нагрузки) и СП 16.13330.2017 (прочность стали).
      </footer>
    </div>
  );
}

function ResultPanel({ result }: { result: CalculationResult }) {
  const { loads, profile, bracket, overallPass, warnings } = result;

  return (
    <>
      <div className="panel">
        <h2>
          Результат расчёта{" "}
          <span className={`verdict ${overallPass ? "pass" : "fail"}`}>
            {overallPass ? "ПРОХОДИТ" : "НЕ ПРОХОДИТ"}
          </span>
        </h2>

        <h3>Нагрузки</h3>
        <table className="loads-table">
          <tbody>
            <tr>
              <td>w₀ (по справочнику города)</td>
              <td>{loads.w0Kpa.toFixed(3)} кПа</td>
            </tr>
            <tr>
              <td>k(z) коэффициент для типа местности</td>
              <td>{loads.kZ.toFixed(3)}</td>
            </tr>
            <tr>
              <td>c — аэродинамический коэффициент</td>
              <td>{loads.c.toFixed(2)}</td>
            </tr>
            <tr>
              <td>γ_f — коэффициент надёжности по нагрузке</td>
              <td>{loads.gammaF.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Пиковое расчётное давление w_расч</td>
              <td>{loads.wPeakPa.toFixed(1)} Па</td>
            </tr>
            <tr>
              <td>q — линейная нагрузка на профиль</td>
              <td>{(loads.qProfileNmm * 1000).toFixed(2)} Н/м</td>
            </tr>
            <tr>
              <td>F — сила на кронштейн</td>
              <td>{loads.fBracketN.toFixed(1)} Н</td>
            </tr>
          </tbody>
        </table>
      </div>

      <ElementResultPanel element={profile} title="Профиль (направляющая)" />
      <ElementResultPanel element={bracket} title="Кронштейн" />

      {warnings.length > 0 && (
        <div className="warn-list">
          <b>Предупреждения:</b>
          <ul>
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}

function ElementResultPanel({
  element,
  title,
}: {
  element: CalculationResult["profile"];
  title: string;
}) {
  return (
    <div className="panel">
      <h2>
        {title}:{" "}
        <span className={`verdict ${element.pass ? "pass" : "fail"}`}>
          {element.pass ? "ПРОХОДИТ" : "НЕ ПРОХОДИТ"}
        </span>
      </h2>
      <p>{element.elementName}</p>

      <table className="checks-table">
        <thead>
          <tr>
            <th>Проверка</th>
            <th>Факт</th>
            <th>Допуск</th>
            <th>Загрузка</th>
            <th>Ссылка</th>
          </tr>
        </thead>
        <tbody>
          {element.checks.map((c, i) => (
            <tr key={i}>
              <td>{c.name}</td>
              <td>
                {c.actual.toFixed(2)} {c.unit}
              </td>
              <td>
                {c.allowable.toFixed(2)} {c.unit}
              </td>
              <td>
                <span className={`util-bar ${c.pass ? "" : "fail"}`}>
                  <span
                    style={{
                      width: `${Math.min(100, c.utilization * 100).toFixed(0)}%`,
                    }}
                  />
                </span>
                {(c.utilization * 100).toFixed(0)}%
              </td>
              <td>
                <small>{c.reference}</small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
