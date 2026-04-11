# ep4.1 ライフイベント家計シミュレーター — 実装・検証

この回では、ep4.0 で作った要件定義をもとに Claude Code で実装し、FP 実務の視点でバリデーション・出力を検証しました。

実装コードは別リポジトリで管理しています。

**[→ t-motoki/demo-life-event-simulator](https://github.com/t-motoki/demo-life-event-simulator)**

---

## この回でやったこと

1. Claude Code に設計図（システム構成図・ドメインモデル図）を出させる
2. さばきゃんにユースケースを確認してもらう（FP が操作・Excel 出力）
3. CLAUDE.md に実装の前提・参照先を整理する
4. 短いプロンプトで実装開始（tester → architect → engineer の順で動く）
5. Excel 出力を確認 → 動いたが FP 実務で使えるかを検証
6. バリデーション・出力の穴を見つけて修正する

---

## Claude Code に渡したプロンプト

### 設計図の生成（S03a）

```
ライフイベント家計シミュレーターのシステム全体構造とドメインモデルを
Mermaid 形式で出力してください。

要件定義書: docs/spec/01_requirements.md
```

### 実装の依頼（S07）

```
/implement
```

（CLAUDE.md に実装フロー・計算モデルの前提・参照先が書いてあるため、これだけで動く）

### バリデーション・出力の修正（S10）

```
以下の2点を修正してください。
1. ローン年数が退職年齢を超える場合にバリデーションエラーを返す
2. 貯蓄残高がマイナスになった時点で警告を出す
```

```
入力確認シートに住宅ローンの完済年齢（借入時年齢 + loan_years）を追加してください。
```

---

## 生成されたファイル

| ファイル | 内容 |
|----------|------|
| [src/domain/models.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/domain/models.py) | ドメインモデル定義 |
| [src/domain/cashflow.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/domain/cashflow.py) | キャッシュフロー計算 |
| [src/domain/loan.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/domain/loan.py) | 住宅ローン控除計算（13年・0.7%） |
| [src/input/validator.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/input/validator.py) | 入力バリデーション |
| [src/output/excel_writer.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/output/excel_writer.py) | Excel 出力 |
| [CLAUDE.md](https://github.com/t-motoki/demo-life-event-simulator/blob/master/CLAUDE.md) | AI への指示書（実装フロー・参照先） |
