// 額面時給・拘束時給の計算ロジック（純粋関数）。
// このファイルが計算の唯一の実装。index.html もテストも、ここの calcHourlyWages だけを呼ぶ。
// DOM・window・グローバル状態には一切触れない（引数だけ受け取り、plain object か null を返す）。

// 入力値を「有限で 0 以上の数値」に正規化する。
// 空文字 "" は Number("") が 0 になってしまうため、ここで先に弾く。
// 数値でない・NaN・Infinity・負値はすべて算出不能を表す null にする。
function toNonNegativeNumber(value) {
  // 空文字・null・undefined は未入力とみなして算出不能。
  if (value === "" || value === null || value === undefined) return null;
  const n = Number(value);
  // 非数・NaN・Infinity を弾く（Number.isFinite は Infinity も false にする）。
  if (!Number.isFinite(n)) return null;
  // 時給計算で負の時間・負の月収は意味を持たないため算出不能。
  if (n < 0) return null;
  return n;
}

/**
 * 額面時給・拘束時給・通勤時間合計を計算する。
 * @param {{monthlyIncome:number, workHours:number, commuteHoursPerDay:number, workDaysPerMonth:number}} input
 * @returns {{faceWage:number, realWage:number, commuteHoursTotal:number} | null}
 *   算出不能（ゼロ除算・負・非数・空・workHours<=0・分母<=0 等）はすべて null。
 *   例外は一切 throw しない。
 */
function calcHourlyWages(input) {
  // 引数自体が無い場合も算出不能。
  if (input === null || input === undefined || typeof input !== "object") {
    return null;
  }

  const monthlyIncome = toNonNegativeNumber(input.monthlyIncome);
  const workHours = toNonNegativeNumber(input.workHours);
  const commuteHoursPerDay = toNonNegativeNumber(input.commuteHoursPerDay);
  const workDaysPerMonth = toNonNegativeNumber(input.workDaysPerMonth);

  // いずれかが正規化できなければ算出不能。
  if (
    monthlyIncome === null ||
    workHours === null ||
    commuteHoursPerDay === null ||
    workDaysPerMonth === null
  ) {
    return null;
  }

  // 額面時給は労働時間で割る。労働時間 0 はゼロ除算なので算出不能。
  if (workHours <= 0) return null;
  const faceWage = monthlyIncome / workHours;

  // 通勤時間合計 = 1日の通勤時間 × 出勤日数。
  const commuteHoursTotal = commuteHoursPerDay * workDaysPerMonth;

  // 拘束時給は「労働時間 + 通勤時間合計」で割る。分母 0 以下なら算出不能。
  const realDenominator = workHours + commuteHoursTotal;
  if (realDenominator <= 0) return null;
  const realWage = monthlyIncome / realDenominator;

  return { faceWage, realWage, commuteHoursTotal };
}

// UMD 風デュアルエクスポート。
// node テストでは require で module.exports を読む。
// ブラウザでは window.Wage に生やし、index.html が <script src> で読んで呼ぶ。
// type="module" を使わないため file:// の CORS 問題に当たらない。
if (typeof module !== "undefined" && module.exports) {
  module.exports = { calcHourlyWages };
} else {
  window.Wage = { calcHourlyWages };
}
