# ep4.3 形を変えよう — FP向けWebアプリへ

この回では、ep4.1/4.2 で作った Python ドメインロジックを触らずに、FP がブラウザで使える Web アプリに仕立て直しました。

実装コードは別リポジトリで管理しています。

**[→ t-motoki/demo-life-event-simulator](https://github.com/t-motoki/demo-life-event-simulator)**

---

## この回でやったこと

1. 「誰のために作るか」を定義し直す（FP が直接操作できる形）
2. セキュリティ要件を最初に決める（データを保存しない・ローカル完結）
3. FastAPI で REST API 層を追加する（既存ドメインロジックは変更しない）
4. React + Vite でフロントエンドを作る（入力フォーム・結果表示）
5. さばきゃんがブラウザで動作確認する

---

## Claude Code に渡したコンテキスト

### FastAPI 実装（S05）

```
ライフイベント家計シミュレーターに Web API 層を追加してください。

前提:
- 既存の計算ロジック（src/domain/cashflow.py の simulate()）は変更しない
- データを保存しない設計（計算して返すだけ）
- 入力・出力の型を明示すること（Pydantic スキーマ）

参照: src/domain/cashflow.py, src/input/validator.py
```

### フロントエンド実装（S05）

```
React + Vite でシミュレーターの入力フォームを作成してください。

要件:
- FP がクライアントとの面談で使うフォーム
- 入力項目: 年齢・収入・配偶者収入・ライフイベント（出産・住宅・教育・老後）
- 結果: 年次キャッシュフロー一覧を表形式で表示
- バックエンド: POST /simulate に送信
```

---

## 実装のポイント

### 計算ロジックを変えない

```python
# コマンドラインから使うとき（ep4.1）
result = simulate(params)

# ブラウザから使うとき（今回）
@app.post("/simulate")
def simulate_endpoint(request: SimulateRequest):
    rows = simulate(to_domain_scenario(request))  # 同じ関数を呼んでいる
    return to_response(rows)
```

CUI と Web API で呼んでいる計算は同じ。「形を変えた」のは入力と出力の形だけ。

### データを保存しない設計

```python
@app.post("/simulate")
def simulate_endpoint(request: SimulateRequest) -> list[CashFlowRowResponse]:
    scenario = to_domain_scenario(request)
    validate(scenario)
    rows = simulate(scenario)
    return to_response(rows)
    # データベースへの保存なし・ログへの記録なし
```

FP が使うローカルツールとして「計算して返すだけ」を最初に決めた。後から変えると影響が大きいため、設計時に判断する。

---

## 生成されたファイル

| ファイル | 内容 |
|----------|------|
| [src/api/main.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/api/main.py) | FastAPI アプリ定義（CORS 設定含む） |
| [src/api/routes/simulate.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/api/routes/simulate.py) | POST /simulate エンドポイント |
| [src/api/schemas.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/api/schemas.py) | Pydantic スキーマ（入出力型定義） |
| [frontend/src/App.tsx](https://github.com/t-motoki/demo-life-event-simulator/blob/master/frontend/src/App.tsx) | React アプリルート |
| [frontend/src/components/](https://github.com/t-motoki/demo-life-event-simulator/blob/master/frontend/src/components/) | 入力セクション・結果表示コンポーネント |
