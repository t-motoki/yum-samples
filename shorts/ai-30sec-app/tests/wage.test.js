// wage.js のテスト。
// node からも <script> からも動くように、require があれば require、なければ window.Wage を使う。
// 外部依存ゼロのため assert ヘルパは自前実装する（許容誤差 1e-6）。
const { calcHourlyWages } =
  typeof require !== "undefined" ? require("../wage.js") : window.Wage;

// --- 最小 assert ヘルパ ---
// 失敗件数をためて、最後にまとめて結果を出す。node では失敗時 process.exit(1)。
const failures = [];

function record(ok, message) {
  if (ok) {
    log(`  OK   ${message}`);
  } else {
    failures.push(message);
    log(`  FAIL ${message}`);
  }
}

// node では console.log、ブラウザでは test.html 側が log を差し替えられるよう関数経由にする。
function log(line) {
  if (typeof console !== "undefined") console.log(line);
}

// 浮動小数の比較は誤差 1e-6 まで許容する（時給は割り算で端数が出るため）。
function assertClose(actual, expected, message) {
  const ok =
    typeof actual === "number" && Math.abs(actual - expected) <= 1e-6;
  record(ok, `${message} (期待≈${expected} / 実際=${actual})`);
}

function assertEqual(actual, expected, message) {
  record(actual === expected, `${message} (期待=${expected} / 実際=${actual})`);
}

function assertNull(actual, message) {
  record(actual === null, `${message} (実際=${JSON.stringify(actual)})`);
}

// --- テスト本体 ---
function runTests() {
  // === 正常系 ===

  // 代表ケース: 月収300000 / 労働160h / 通勤往復1.5h / 出勤20日
  // faceWage = 300000 / 160 = 1875
  // commuteHoursTotal = 1.5 * 20 = 30
  // realWage = 300000 / (160 + 30) = 1578.947...
  {
    const r = calcHourlyWages({
      monthlyIncome: 300000,
      workHours: 160,
      commuteHoursPerDay: 1.5,
      workDaysPerMonth: 20,
    });
    assertClose(r && r.faceWage, 1875, "代表ケース: faceWage");
    assertClose(r && r.commuteHoursTotal, 30, "代表ケース: commuteHoursTotal");
    assertClose(r && r.realWage, 300000 / 190, "代表ケース: realWage");
  }

  // 通勤0なら 額面 = 拘束
  {
    const r = calcHourlyWages({
      monthlyIncome: 300000,
      workHours: 160,
      commuteHoursPerDay: 0,
      workDaysPerMonth: 20,
    });
    assertClose(r && r.commuteHoursTotal, 0, "通勤0: commuteHoursTotal=0");
    assertClose(r && r.faceWage, 1875, "通勤0: faceWage");
    assertEqual(
      r && r.realWage,
      r && r.faceWage,
      "通勤0: realWage === faceWage"
    );
  }

  // 通勤時間合計 = 1日の通勤 × 出勤日数
  {
    const r = calcHourlyWages({
      monthlyIncome: 250000,
      workHours: 150,
      commuteHoursPerDay: 2,
      workDaysPerMonth: 22,
    });
    assertClose(r && r.commuteHoursTotal, 44, "通勤合計 = 2 * 22 = 44");
  }

  // 小数入力でも計算できる
  {
    const r = calcHourlyWages({
      monthlyIncome: 320000.5,
      workHours: 162.5,
      commuteHoursPerDay: 0.75,
      workDaysPerMonth: 21,
    });
    const expectedFace = 320000.5 / 162.5;
    const expectedCommute = 0.75 * 21;
    const expectedReal = 320000.5 / (162.5 + expectedCommute);
    assertClose(r && r.faceWage, expectedFace, "小数入力: faceWage");
    assertClose(r && r.commuteHoursTotal, expectedCommute, "小数入力: commuteHoursTotal");
    assertClose(r && r.realWage, expectedReal, "小数入力: realWage");
  }

  // 月収0は時給0（null ではない）。労働時間が正なら算出可能。
  {
    const r = calcHourlyWages({
      monthlyIncome: 0,
      workHours: 160,
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    });
    assertEqual(r && r.faceWage, 0, "月収0: faceWage=0（nullでない）");
    assertEqual(r && r.realWage, 0, "月収0: realWage=0（nullでない）");
  }

  // === 異常系（例外を投げず null を返す）===

  // 労働0 → faceWage 算出不能 → null
  assertNull(
    calcHourlyWages({
      monthlyIncome: 300000,
      workHours: 0,
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    }),
    "労働0 → null"
  );

  // 分母0（労働0かつ通勤0）→ realWage 算出不能 → null
  assertNull(
    calcHourlyWages({
      monthlyIncome: 300000,
      workHours: 0,
      commuteHoursPerDay: 0,
      workDaysPerMonth: 0,
    }),
    "分母0 → null"
  );

  // 負入力 → null
  assertNull(
    calcHourlyWages({
      monthlyIncome: 300000,
      workHours: -10,
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    }),
    "労働時間が負 → null"
  );
  assertNull(
    calcHourlyWages({
      monthlyIncome: -300000,
      workHours: 160,
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    }),
    "月収が負 → null"
  );
  assertNull(
    calcHourlyWages({
      monthlyIncome: 300000,
      workHours: 160,
      commuteHoursPerDay: -1,
      workDaysPerMonth: 20,
    }),
    "通勤時間が負 → null"
  );
  assertNull(
    calcHourlyWages({
      monthlyIncome: 300000,
      workHours: 160,
      commuteHoursPerDay: 1,
      workDaysPerMonth: -5,
    }),
    "出勤日数が負 → null"
  );

  // 非数・空 → null（例外を投げない）
  assertNull(
    calcHourlyWages({
      monthlyIncome: NaN,
      workHours: 160,
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    }),
    "月収がNaN → null"
  );
  assertNull(
    calcHourlyWages({
      monthlyIncome: "",
      workHours: 160,
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    }),
    "月収が空文字 → null"
  );
  assertNull(
    calcHourlyWages({
      monthlyIncome: 300000,
      workHours: "",
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    }),
    "労働時間が空文字 → null"
  );
  assertNull(
    calcHourlyWages({
      monthlyIncome: 300000,
      workHours: Infinity,
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    }),
    "労働時間がInfinity → null"
  );
  assertNull(
    calcHourlyWages({
      monthlyIncome: "abc",
      workHours: 160,
      commuteHoursPerDay: 1,
      workDaysPerMonth: 20,
    }),
    "月収が文字列 → null"
  );
  assertNull(calcHourlyWages(null), "引数null → null");
  assertNull(calcHourlyWages(undefined), "引数undefined → null");

  // === 不変条件 ===
  // 通勤 > 0 のとき realWage <= faceWage（拘束時間が増えるので時給は下がる）
  {
    const cases = [
      { monthlyIncome: 300000, workHours: 160, commuteHoursPerDay: 1.5, workDaysPerMonth: 20 },
      { monthlyIncome: 500000, workHours: 200, commuteHoursPerDay: 2, workDaysPerMonth: 22 },
      { monthlyIncome: 180000, workHours: 120, commuteHoursPerDay: 0.5, workDaysPerMonth: 18 },
    ];
    cases.forEach((input, i) => {
      const r = calcHourlyWages(input);
      const ok = r && r.realWage <= r.faceWage;
      record(ok, `不変条件[${i}]: 通勤>0 で realWage <= faceWage`);
    });
  }

  // --- 結果サマリ ---
  if (failures.length === 0) {
    log("\n全テスト通過 ✅");
  } else {
    log(`\n${failures.length} 件のテストが失敗 ❌`);
  }
  return failures.length;
}

// node 実行時はその場で走らせて exit code を立てる。
// ブラウザ（test.html）からは runTests を呼べるように公開する。
if (typeof module !== "undefined" && module.exports) {
  module.exports = { runTests };
  const failed = runTests();
  if (failed > 0) process.exit(1);
} else {
  window.WageTest = { runTests, setLog: (fn) => (log = fn) };
}
