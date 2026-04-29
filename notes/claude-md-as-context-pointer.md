# CLAUDE.md はコンテキストへのポインタ

ep4.1 で実践した CLAUDE.md の設計パターン。

---

## 問題

CLAUDE.md に要件・ルール・計算モデルを直接書くと：

- 更新のたびに CLAUDE.md が肥大化する
- 「どこに何があるか」が一目でわからなくなる
- 内容が古くなっても気づきにくい

---

## 解決策: CLAUDE.md はポインタのみ

実体は `docs/` 以下に分散させ、CLAUDE.md には「何をどこで読むか」だけを書く。

```markdown
## 実装前に必ず読む

| ファイル | 内容 |
|----------|------|
| docs/spec/01_requirements.md § 7 | FP確認済みの計算モデル |
| docs/spec/01_requirements.md § 8 | 未確定事項 |
| docs/rules/00_workflow.md | 実装フロー・エージェント定義 |
| docs/rules/03_validation.md | バリデーション項目・エラーメッセージ |
```

---

## メリット

- CLAUDE.md が腐らない（ポインタだけなので更新頻度が低い）
- 実体ファイルは独立して更新できる
- AI は「何を読むか」を CLAUDE.md から知り、詳細は実体ファイルから取得する

---

## 関連

- [demo-life-event-simulator/CLAUDE.md](https://github.com/t-motoki/demo-life-event-simulator/blob/master/CLAUDE.md)
