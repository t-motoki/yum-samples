// AI作業対象外・独立オラクル（held-out）のランナー。
//
// 作業ツリーの検査3種（npm test / lint / typecheck）とは別系統。AIに渡す検査群には含めない。
// 各テイク末に人間が回し、workspace の src/kaikei.js が本当の要件に適合しているかを独立に判定する。
//
// 検証対象の src は --workdir で受ける（作業ツリーは既定でリポジトリ外にあるため）。
// 期待値は隣の acceptance.golden（SPEC から人手導出）を読む。src の出力からは作らない。
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import { createRequire } from "node:module";

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

// --workdir <path>: 検証対象 workspace（kaikei ディレクトリ）のパス。
function parseWorkdir(argv) {
  const i = argv.indexOf("--workdir");
  if (i === -1 || !argv[i + 1]) {
    console.error("使い方: node verify-oracle.mjs --workdir <workspaceのパス>");
    process.exit(2);
  }
  return resolve(argv[i + 1]);
}

const workdir = parseWorkdir(process.argv.slice(2));
const target = join(workdir, "src", "kaikei.js");
const { splitBill } = require(target);
const golden = JSON.parse(readFileSync(join(here, "acceptance.golden"), "utf8"));

const failures = [];
function check(ok, message) {
  console.log(`  ${ok ? "OK  " : "FAIL"} ${message}`);
  if (!ok) failures.push(message);
}

function arrayEquals(a, b) {
  return (
    Array.isArray(a) &&
    Array.isArray(b) &&
    a.length === b.length &&
    a.every((v, i) => v === b[i])
  );
}

console.log(`--- 検証対象: ${target} ---`);
console.log("--- 代表ベクトル（SPEC から人手導出）---");
for (const { total, n, expected } of golden.representative) {
  const actual = splitBill(total, n);
  check(
    arrayEquals(actual, expected),
    `splitBill(${total}, ${n}) = ${JSON.stringify(actual)}（期待 ${JSON.stringify(expected)}）`,
  );
}

console.log("--- プロパティ（保存則ほか）---");
for (const { total, n } of golden.propertyCases) {
  const parts = splitBill(total, n);
  const sum = parts.reduce((acc, v) => acc + v, 0);
  check(sum === total, `保存則 sum=${sum} === total=${total}  [total=${total}, n=${n}]`);
  check(parts.length === n, `要素数 length=${parts.length} === n=${n}  [total=${total}, n=${n}]`);
  const max = Math.max(...parts);
  const min = Math.min(...parts);
  check(max - min <= 1, `公平性 max-min=${max - min} <= 1  [total=${total}, n=${n}]`);
  check(
    parts.every((v) => Number.isInteger(v) && v >= 0),
    `非負整数  [total=${total}, n=${n}]`,
  );
}

console.log("");
if (failures.length > 0) {
  console.error(`独立オラクル: ${failures.length} 件の仕様違反を検出しました。`);
  process.exit(1);
} else {
  console.log("独立オラクル: すべて仕様に適合しています。");
}
