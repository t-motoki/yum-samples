const {
  perPersonBase,
  remainder,
  splitBill,
  sumSplit,
} = require("../src/kaikei.js");

describe("splitBill（割り勘の内訳）", () => {
  test("1000円を3人で割ると [334, 333, 333]", () => {
    expect(splitBill(1000, 3)).toEqual([334, 333, 333]);
  });

  test("内訳の合計は元の金額と一致する", () => {
    expect(sumSplit(splitBill(1000, 3))).toBe(1000);
  });

  test("割り切れる場合は全員同額", () => {
    expect(splitBill(1000, 4)).toEqual([250, 250, 250, 250]);
  });

  test("1001円を3人で割ると [334, 334, 333]", () => {
    expect(splitBill(1001, 3)).toEqual([334, 334, 333]);
  });

  test("要素数は人数と一致する", () => {
    expect(splitBill(1000, 3).length).toBe(3);
  });
});

describe("perPersonBase / remainder（基本額・余り）", () => {
  test("基本額は切り捨て", () => {
    expect(perPersonBase(1000, 3)).toBe(333);
  });

  test("余りは割った余り", () => {
    expect(remainder(1000, 3)).toBe(1);
  });
});
