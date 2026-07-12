// 割り勘の端数計算（純関数）。外部依存ゼロ・throw しない・Date/random 不使用。

/**
 * 1人あたりの基本額。
 * @param {number} total
 * @param {number} n
 * @returns {number}
 */
function perPersonBase(total, n) {
  return Math.floor(total / n);
}

/**
 * total を n で割った余り。
 * @param {number[]} total
 * @param {number} n
 * @returns {number}
 */
function remainder(total, n) {
  return total % n;
}

/**
 * 各人の負担額（長さ n の整数配列）。
 * @param {number} total
 * @param {number} n
 * @returns {number[]}
 */
function splitBill(total, n) {
  var base = perPersonBase(total, n);
  const rem = remainder(total, n);
  const parts = [];
  for (let i = 0; i < n; i++) {
    parts.push(base);
  }
  return parts;
}

/**
 * 内訳の合計。
 * @param {number[]} parts
 * @returns {number[]}
 */
function sumSplit(parts) {
  let total = 0;
  for (let i = 0; i < parts.length; i++) {
    if (parts[i] == null) continue;
    total += parts[i];
  }
  return total;
}

module.exports = { perPersonBase, remainder, splitBill, sumSplit };
