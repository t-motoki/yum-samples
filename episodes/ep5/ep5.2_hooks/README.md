# ep5.2 hooks — 書き方を変えると、動き方が変わる

この回では、Claude Code の hooks（`PreToolUse` / `PostToolUse`）を使って「AIがやろうとした瞬間に動く」仕掛けを作りました。  
CLAUDE.md（宣言型ガード）との違いと、life-event-simulator での実装例を見せています。

---

## この回でやったこと

1. CLAUDE.md に「FP確認が必要な計算は変えるな」と書いても守られなかった事例を示す
2. PreToolUse hook で `src/domain/` への変更を事前にチェックする仕掛けを入れた
3. PostToolUse hook で変更後に pytest を自動実行する仕掛けを入れた
4. CLAUDE.md（信頼に依存）と hooks（強制実行）の使い分けを整理する

---

## hooks とは

Claude Code には、ツール実行の前後に任意のシェルコマンドを実行できる仕組みがある。

| hook 種別 | 発火タイミング | 主な用途 |
|-----------|--------------|---------|
| `PreToolUse` | Claude がツールを**使おうとする前** | 禁止チェック・確認促進・ブロック |
| `PostToolUse` | Claude がツールを**使い終わった後** | 自動テスト・ログ記録・後処理 |

設定は `.claude/settings.json` に書く。プロジェクトルートに置くとそのプロジェクトに適用される。

---

## life-event-simulator での実装

`.claude/settings.json` → [`settings.json`](./.claude/settings.json)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'check-fp-pending.sh'"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'run-tests-if-src.sh'"
          }
        ]
      }
    ]
  }
}
```

---

### PreToolUse — FP未確認事項ガード

**目的**: FP（ファイナンシャルプランナー）に確認が必要な計算を、AIが独断で変更しないようにする。

`src/domain/` 配下（計算ロジック層）への変更を試みたとき、要件書に `TODO: FPに確認` が残っていれば警告を出す。

```bash
# 動作の流れ
1. Claude が src/domain/maternity_leave.py を Edit しようとする
2. PreToolUse hook が発火する
3. "$CLAUDE_TOOL_INPUT_FILE_PATH" を確認 → "src/domain/" を含む
4. docs/spec/01_requirements.md に "TODO: FPに確認" があるかチェック
5. あれば → 警告メッセージを出力（Claude はこれを読んで実装を止める）
6. なければ → 何も起きずに通過
```

**ポイント**: hook はメッセージを出力するだけ。実装を止めるかどうかは Claude が判断する。  
「何を止めるかはコードが決め、何を止めるかはゆむが設計した」という関係になっている。

---

### PostToolUse — 変更後に自動テスト

**目的**: `src/` 配下のファイルを変更したあと、毎回 pytest を自動実行する。

手動で `pytest` を実行し忘れたり、変更が積み重なってテストを通すのが難しくなる前に、1変更ごとに確認できる。

```bash
# 動作の流れ
1. Claude が src/calculator.py を Edit し終わる
2. PostToolUse hook が発火する
3. "$CLAUDE_TOOL_INPUT_FILE_PATH" が "src/" で始まるか確認
4. pytest を実行 → 結果を出力（Claude が読んで次の判断に使う）
```

---

## CLAUDE.md vs hooks

| | CLAUDE.md | hooks |
|--|-----------|-------|
| 動くタイミング | セッション開始時に読む | ツール実行の前後に毎回 |
| 強制力 | 弱（読み飛ばされることがある） | 強（必ず発火する） |
| 向いている内容 | 方針・優先度・参照先 | 具体的な禁止チェック・自動処理 |
| 変更コスト | ファイルを編集するだけ | コマンドのロジックを書く必要がある |

**使い分け**: CLAUDE.md で「何のために・どこを見るか」を伝え、hooks で「やろうとした瞬間に止まる」仕掛けを作る。  
片方は信頼して、もう一方は仕掛けで補う。

---

## 設定ファイルの書き方

**配置場所**: プロジェクトルートの `.claude/settings.json`

**環境変数**（hook コマンド内で使えるもの）:

| 変数 | 内容 |
|------|------|
| `$CLAUDE_TOOL_NAME` | 発火したツール名（`Edit`, `Write`, `Bash` など） |
| `$CLAUDE_TOOL_INPUT_FILE_PATH` | 操作対象のファイルパス（Edit/Write のとき） |

**matcher の書き方**:

```json
"matcher": "Edit|Write"     // Edit または Write のとき
"matcher": "Bash"           // Bash コマンド実行のとき
"matcher": ".*"             // 全ツール
```

**注意**: hook のコマンドが終了コード 0 以外を返すと Claude Code はエラーとして扱う。  
警告だけ出したいとき（ブロックしたくないとき）は `|| true` で必ず終了コード 0 を返すようにする。

```bash
# 警告だけ出してブロックしない（|| true が重要）
bash -c '... && echo "警告: ..." || true'

# ブロックしたいとき（exit 1 を返す）
bash -c '... && exit 1'
```

---

## サンプルファイル

[`.claude/settings.json`](./.claude/settings.json) — PreToolUse + PostToolUse の設定例（パスを自プロジェクト向けに書き換えて使う）
