# ep3.0 紙芝居スタイル動画パイプライン

動画「紙芝居スタイル動画パイプライン — 台本を書けばゆむが感情豊かに話す仕組みを作る」のサンプルコードです。

## この動画でやること

台本の各ナレーション行に `<!-- expression: joy -->` のようなディレクティブを書くだけで、
文ごとにアバターの表情が切り替わる動画が自動生成できるパイプラインを構築します。

```
script.md（ディレクティブ入り）→ パーサー → Scene列（表情付き）→ 動画
```

## 追加した機能

### 1. `AvatarConfig` に6表情を追加（`entities.py`）

```python
@dataclass
class AvatarConfig:
    normal: Path | None = None    # stand.png
    smile: Path | None = None     # relax.png
    surprise: Path | None = None  # surprise.png
    chibi: Path | None = None     # chibi.png
    joy: Path | None = None       # joy.png      ← 追加
    angry: Path | None = None     # angry.png    ← 追加
    thinking: Path | None = None  # thinking.png ← 追加

    def get(self, expression: str) -> Path | None:
        return getattr(self, expression, None) or self.normal
```

`get()` は `getattr` ベースなので、フィールドを追加するだけで対応完了です。

### 2. `<!-- expression: xxx -->` ディレクティブのパース（`markdown_reader.py`）

台本 Markdown にこう書くと：

```markdown
今回は6種の表情が揃いました。
<!-- expression: joy -->
表情豊かな動画パイプライン、完成です！
<!-- expression: thinking -->
次はどんな演出ができるでしょうか。
<!-- expression: reset -->
デフォルトに戻ります。
```

各文の `Scene.avatar_expression` が自動的に設定されます：

```
_00: normal  — 今回は6種の表情が揃いました。
_01: joy     — 表情豊かな動画パイプライン、完成です！
_02: thinking — 次はどんな演出ができるでしょうか。
_03: normal  — デフォルトに戻ります。
```

## サンプルコード

`expression_demo.py` — ディレクティブのパース動作を単体で確認できるデモスクリプトです。

```bash
python expression_demo.py
```

## 使える表情一覧

| 表情 | ファイル名 | 主な用途 |
|------|----------|---------|
| normal | stand.png | デフォルト |
| smile | relax.png | やわらかい説明・余談 |
| surprise | surprise.png | 驚き・強調 |
| chibi | chibi.png | イントロ/アウトロ（自動付与） |
| joy | joy.png | 喜び・成功 |
| angry | angry.png | 問題提起・強い主張 |
| thinking | thinking.png | 考察・疑問 |

## ライセンス

MIT License
