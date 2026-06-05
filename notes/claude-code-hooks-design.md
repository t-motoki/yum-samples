# Claude Code hooks 設計パターン — PreToolUse と PostToolUse の使い分け

## 背景

ep5.2 で取り上げた「AIがやろうとした瞬間に止まる仕掛け」の設計判断を記録する。  
CLAUDE.md（宣言型ガード）との使い分けが核心。

---

## hooks の位置づけ

CLAUDE.md は「読まれることを前提とした宣言」。セッション開始時に Claude が読むが、読み飛ばされることがある。  
hooks は「ツール実行のたびに強制的に実行されるコマンド」。宣言を信じるのではなく、動作として埋め込む。

```
CLAUDE.md: 「FP確認が必要な計算は変えるな」 → 読まれないと機能しない
hooks:      Edit しようとした瞬間にチェックが走る → 読まずに通過できない
```

どちらかが優れているわけではなく、信頼できる領域と強制が必要な領域で使い分ける。

---

## PreToolUse — 「変える前に止める」パターン

**発火タイミング**: Claude がツールを呼ぶ直前。

**典型的な用途**:
- 「この種のファイルは触るな」というルールを機械的に強制したいとき
- 未確認事項（TODO・pending 項目）が残っているとき、実装をブロックしたいとき
- 高リスクな操作（本番 DB・認証ロジック）の前に確認を促したいとき

**設計の考え方**:

```bash
# パターン: 対象ファイルのチェック → 状態チェック → メッセージ出力
bash -c '
  echo "$CLAUDE_TOOL_INPUT_FILE_PATH" | grep -q "^src/domain/" &&
  grep -q "TODO: FPに確認" ./docs/spec/01_requirements.md &&
  echo "警告: FP未確認事項が残っています。確認を取ってから進めてください。" ||
  true
'
```

- `&&` でチェックを連鎖させる。すべての条件が揃ったときだけ警告を出す
- 末尾の `|| true` で終了コードを 0 に保つ（ブロックではなく警告のみの場合）
- ブロックしたいなら `exit 1` を返す（Claude Code がエラーとして扱い、操作を止める）

**注意**: メッセージを出力するだけでは Claude が「無視して進める」こともある。  
確実にブロックしたい場合は `exit 1` を返す。警告だけでよい場合は `|| true`。

---

## PostToolUse — 「変えた後に確かめる」パターン

**発火タイミング**: Claude がツールを呼び終わった直後。

**典型的な用途**:
- ファイル変更のたびにテストを自動実行したいとき
- 変更のログを残したいとき
- lint や型チェックを毎回走らせたいとき

**設計の考え方**:

```bash
# パターン: 対象ファイルの範囲チェック → 自動処理実行
bash -c '
  echo "$CLAUDE_TOOL_INPUT_FILE_PATH" | grep -q "^src/" &&
  python -m pytest tests/ -q --tb=short 2>&1 ||
  true
'
```

- `src/` 配下への変更のときだけ pytest を走らせる（全ファイル変更で走ると遅い）
- テスト失敗は exit コードに関わらず出力として Claude に届く
- `2>&1` で stderr も流すことで、エラーメッセージを Claude が読める

---

## 2つを組み合わせる

```
Edit/Write しようとする
     ↓
PreToolUse が発火
  → 条件に引っかかれば警告またはブロック
     ↓（通過したら）
実際に Edit/Write が実行される
     ↓
PostToolUse が発火
  → テスト自動実行・結果を Claude に渡す
```

「変える前に止める」と「変えた後に確かめる」の組み合わせで、変更の前後を両方カバーできる。

---

## matcher の設計

```json
"matcher": "Edit|Write"     // ファイル書き込み系のみ
"matcher": "Bash"           // シェルコマンド実行のとき
"matcher": ".*"             // 全ツール（コスト高い処理には使わない）
```

PostToolUse で全ツールに pytest を走らせると、Read ツールのたびにテストが実行されて遅くなる。  
`Edit|Write` に絞ることで「変更があったときだけ」に限定できる。

---

## 環境変数

| 変数 | 型 | 内容 |
|------|-----|------|
| `$CLAUDE_TOOL_NAME` | string | 発火したツール名（`Edit`, `Write`, `Bash` など） |
| `$CLAUDE_TOOL_INPUT_FILE_PATH` | string | 操作対象のファイルパス（Edit/Write のとき） |

`$CLAUDE_TOOL_INPUT_FILE_PATH` は相対パスで渡される（プロジェクトルート基準）。  
そのため `grep -q "^src/"` のように先頭マッチで判定できる。

---

## 落とし穴

**絶対パスのハードコード**

hooks コマンド内でプロジェクトの絶対パスをハードコードすると、別マシンや別ディレクトリに clone したときに動かない。  
`$(pwd)` や `cd` を使って相対的に解決するか、環境変数で外出しする設計にする。

```bash
# 悪い例
cd /home/user/my-project && python -m pytest

# 良い例（プロジェクトルートへ cd してから実行）
bash -c 'echo "$CLAUDE_TOOL_INPUT_FILE_PATH" | grep -q "^src/" && python -m pytest tests/ -q --tb=short 2>&1 || true'
# ↑ Claude Code はプロジェクトルートで hook を実行するため、相対パスが使える
```

**hook が重くなる**

PostToolUse の hook に全テストスイートを走らせると、変更のたびに数分待つことになる。  
`-k` オプションで関連テストだけに絞るか、高速な smoke test だけを hook にする。

```bash
# 重い（全テスト）
python -m pytest tests/ -q

# 軽い（変更ファイルに関連するテストだけ）
python -m pytest tests/ -q -k "$(echo $CLAUDE_TOOL_INPUT_FILE_PATH | sed 's|src/||; s|\.py$||; s|/|_|g')" 2>&1 || true
```

---

## 参照

- [ep5.2 サンプル: life-event-simulator の hooks 設定](../episodes/ep5/ep5.2_hooks/)
- [ep5.0: Claude Code が自律的に動けた理由](../episodes/ep5/ep5.0_claude-code-autonomous-reasons/)
- [CLAUDE.md をポインタとして使う設計](./claude-md-as-context-pointer.md)
