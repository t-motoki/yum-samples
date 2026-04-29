# 台本ディレクティブの設計 — Markdown コメントで動画を制御する

動画生成パイプラインでは、台本（Markdown ファイル）の HTML コメントを
「設定ディレクティブ」として使い、コードを変えずに動画の演出を制御しています。
この設計の考え方を記録します。

## 基本的な考え方

```markdown
<!-- config: telop_fade=normal -->
<!-- bgm: inputs/bgm/relax.mp3 -->
<!-- bgm-fade: 2.0 -->
<!-- thumbnail-subtext: さばきゃん、はじめまして -->
```

HTML コメントは Markdown レンダラーには無視されるため、
台本を人間が読むときは見えないが、パイプラインは読み取れる。

## なぜ YAML フロントマターではなくコメントか

```yaml
# YAML フロントマター（採用しなかった）
---
bgm: inputs/bgm/relax.mp3
bgm_fade: 2.0
telop_fade: normal
---
```

フロントマターは「ファイル全体の設定」には向いているが、
**シーンごとに変えたい設定**（BGM の切り替えなど）を表現しにくい。
コメントはシーンの直前に書けば「ここから変わる」が自然に表現できる。

```markdown
## シーン1: イントロ
<!-- bgm: op_theme.mp3, bgm-fade-in: 1.0 -->

ゆむ「今日はさばきゃんを紹介します」

## シーン2: デモ
<!-- bgm: ambient.mp3 -->

ゆむ「では実際に動かしてみましょう」
```

## パースの実装

正規表現は使わず、`str.startswith()` と `str.removeprefix()` の組み合わせで処理する。

```python
for line in lines:
    line = line.strip()

    if line.startswith("<!-- bgm:"):
        bgm_path = line.removeprefix("<!-- bgm:").removesuffix("-->").strip()

    elif line.startswith("<!-- bgm-fade:"):
        fade_sec = float(
            line.removeprefix("<!-- bgm-fade:").removesuffix("-->").strip()
        )

    elif line.startswith("<!-- thumbnail-subtext:"):
        subtext = line.removeprefix("<!-- thumbnail-subtext:").removesuffix("-->").strip()
```

正規表現を使わないことで:
- コードが読みやすい（`removeprefix` / `removesuffix` は Python 3.9+）
- デバッグが容易（マッチしない理由がすぐわかる）
- 誤マッチのリスクがない

## 主なディレクティブ一覧

| ディレクティブ | 意味 | 例 |
| --- | --- | --- |
| `<!-- config: telop_fade=X -->` | テロップフェード速度 | `fast` / `normal` / `slow` / `none` |
| `<!-- bgm: PATH -->` | BGM ファイルパス | `<!-- bgm: inputs/bgm/relax.mp3 -->` |
| `<!-- bgm-fade: SEC -->` | BGM フェード秒数（全体） | `<!-- bgm-fade: 2.0 -->` |
| `<!-- bgm-fade-in: SEC -->` | BGM フェードイン秒数（シーン単位） | `<!-- bgm-fade-in: 1.0 -->` |
| `<!-- thumbnail-subtext: TEXT -->` | サムネイルのサブテキスト | 空文字でサブテキスト非表示 |
| `<!-- pause: SEC -->` | ナレーションなしの間（秒） | `<!-- pause: 3 -->` |
| `<!-- expression: NAME -->` | キャラクター表情 | `surprise` / `smile` / `thinking` |

## 設計上のトレードオフ

**メリット:**
- 台本ファイル1つで演出まで制御できる（設定ファイルが分散しない）
- 台本を読みながら演出意図が把握できる
- 非エンジニアでも `<!-- bgm: bgm.mp3 -->` と書くだけで使える

**デメリット:**
- ディレクティブの書き方を覚える必要がある
- タイポしてもエラーにならず無視される（サイレントフォール）
- IDE の補完が効かない

## サイレントフォールの対策

ディレクティブを書いたのに効いていないとき、原因がわかりにくい。
`validate_episode.py` を使って台本のディレクティブを事前チェックする。

```bash
python scripts/validate_episode.py inputs/<ep_id>/script.md
```

未知のディレクティブ名や存在しないファイルパスを事前に検出する。
