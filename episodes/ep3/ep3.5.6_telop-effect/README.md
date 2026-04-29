# ep3.5.6 テロップエフェクトディレクティブ

動画「テロップが動く — 4種類のアニメーションを台本から制御する」のサンプルコードです。

台本に `<!-- telop_effect: xxx -->` と書くだけで、テロップの表示アニメーションを4種類から選べる仕組みを実装しました。

## 使い方（台本）

```markdown
<!-- telop_effect: typewriter -->
文字が左から1文字ずつ出てきます。

<!-- telop_effect: slide-in -->
テロップが画面の下からスライドして入ります。

<!-- telop_effect: bounce -->
テロップが弾むように出てきます。

<!-- telop_effect: highlight-word -->
<!-- telop_highlight: 重要, エフェクト -->
重要な単語とエフェクトという言葉が黄色でハイライトされます。
```

スコープはセクション（`##`）単位。またいでは引き継がれません。

## 4種類のエフェクト

| エフェクト名 | 動き | 向いている場面 |
| --- | --- | --- |
| `typewriter` | 文字が左から1文字ずつ出現 | 強調したいセリフ・キーワードの提示 |
| `slide-in` | テロップが下からスライドイン | 新しい話題の開始・セクションの切れ目 |
| `bounce` | テロップが弾んで出現（減衰正弦波） | オチ・インパクトを出したいシーン |
| `highlight-word` | 指定単語を黄色でハイライト（静的） | 専門用語の初出・重要語の強調 |

## 仕組み

```
台本テキスト
    ↓ パーサーが <!-- telop_effect: xxx --> を読む
TelopEffectConfig(effect="typewriter", highlight_words=[])
    ↓ Scene.telop_effect フィールドに格納
PillowRenderer._draw_telop_bar(frame, scene, t=0.3)
    ↓ t（シーン内経過秒）のみで状態を決定（純粋関数）
フレームにテロップを描画
```

アニメーションの現在状態は `t`（シーン内経過秒）のみで決まります。
外部状態に依存しないため、マルチプロセスでのフレームレンダリングでも正しく動作します。

## エフェクトの計算式

### typewriter
```python
n_chars = math.floor(len(text) * t / duration)
display_text = text[:n_chars]
```

### slide-in（ease-out）
```python
progress = min(t / DURATION, 1.0)
eased = 1.0 - (1.0 - progress) ** 2
y_offset = int(TELOP_BAR_H * (1.0 - eased))
```

### bounce（減衰正弦波）
```python
A, k, omega = 30.0, 4.0, 12.0
y_offset = int(A * math.exp(-k * t) * math.sin(omega * t + math.pi / 2))
```
- `A`: 初期振幅（px）
- `k`: 減衰係数（大きいほど早く収束）
- `omega`: 角周波数（大きいほど振動が速い）
- 位相 `π/2` を加えることで `t=0` でオフセット最大から始まる

### highlight-word
```python
x_start = TELOP_PADDING_X + draw.textlength(line[:idx], font=font)
x_end = x_start + draw.textlength(word, font=font)
draw.rectangle([(x_start, y), (x_end, y + font_size)], fill=(255, 215, 0, 200))
draw.text((x_start, y), word, font=font, fill=(0, 0, 0, 255))
```

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `telop_effect_demo.py` | パーサー・レンダラー・CLI のスタンドアロンデモ |

## 動かし方

```bash
# 4種類のエフェクトを t=0〜2.0 秒のフレームとして output/ に出力する
python telop_effect_demo.py render --text "テロップのアニメーションをテストします"

# 特定エフェクトだけ出力する
python telop_effect_demo.py render --effect typewriter --text "タイプライターのデモ"

# highlight-word で単語をハイライトする
python telop_effect_demo.py render --effect highlight-word --text "重要な単語を強調する" --words "重要"

# パーサーの動作を確認する（画像出力なし）
python telop_effect_demo.py parse
```

## 必要なもの

```
pip install pillow numpy
```
