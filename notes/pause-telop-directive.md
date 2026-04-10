# pause シーンにテロップを表示する — `<!-- telop: テキスト -->` ディレクティブ

## 背景

`<!-- pause: N -->` ディレクティブは「ナレーションなしで N 秒間静止する」ためのものです。
ナレーションテキストが空であるため、従来の実装ではテロップ描画のトリガーが発火せず、pause シーン中はテロップが表示されませんでした。

ウェイト中に画面上でも何かが起きていてほしい（「実装中…」という表示を出したい、など）場合に困るケースが発生しました。

---

## 解決策

`<!-- pause: N -->` の直前に `<!-- telop: テキスト -->` を書くと、その pause シーンにテロップが表示されます。

```markdown
<!-- telop: Claude Code 実装中… -->
<!-- pause: 3.0 -->
```

テキストは `narration.text` に直接渡します。レンダラー側の変更は不要です。

---

## 設計のポイント

### narration.text に渡すだけ

pause シーンのテロップ表示は、特別な描画パスを追加していません。
`telop:` ディレクティブが検出されたとき、その値を次のシーンの `narration.text` にセットするだけです。
テロップ描画ロジックはすでに `narration.text` を見ているため、レンダラーは変更ゼロで動きます。

### one-shot（1つの pause にのみ適用）

`telop:` ディレクティブは one-shot です。
適用先の pause シーンが終わると、テロップ値はリセットされます。
次のシーンには引き継がれません。

セクション切り替え（`<!-- section: ... -->`）が起きた場合もリセットされます。

---

## 使用例（台本）

```markdown
<!-- speaker: yumu -->
じゃあ実装してみます。

<!-- telop: Claude Code 実装中… -->
<!-- pause: 4.0 -->

<!-- speaker: yumu -->
できました。
```

pause の 4 秒間、画面に「Claude Code 実装中…」が表示されます。

---

## 注意点

### TTS は走らない

`narration.text` にテキストが入っていても、`duration_sec` が設定されているシーンは TTS を呼ばないガードが入っています。
pause シーンは `duration_sec` で判別されるため、テロップ用テキストがあっても音声は生成されません。

### 衝突回避: `<!-- telop: hidden -->` / `<!-- telop: show -->` との順序

`telop:` ディレクティブは `hidden` / `show` という既存のキーワードとも衝突しうる書き方です。
パース時は `hidden` / `show` を先にマッチさせ、それ以外のテキストを「pause テロップ用テキスト」として扱います。

```python
# パース順の例（概念）
if value in ("hidden", "show"):
    handle_visibility(value)
else:
    set_next_pause_telop(value)
```

---

## 関連ドキュメント

- 設計詳細: `docs/design/pause_telop_directive.md`
- 台本ディレクティブ全般の設計: [台本ディレクティブの設計](./script-directive-design.md)
- ディレクティブのスコープ設計: [ディレクティブのスコープ設計](./directive-scope-design.md)
