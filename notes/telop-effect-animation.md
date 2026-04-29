# テロップエフェクトアニメーションの設計

## 問題

静止テロップ（フェードインのみ）では視線を誘導できない。技術系の動画では「ここだ」という瞬間に動きをつけることで、情報の伝わり方が変わる。

## 解決策: `<!-- telop_effect: xxx -->` ディレクティブ

4種類のアニメーションを台本から選べるようにした。

```markdown
<!-- telop_effect: typewriter -->   # 1文字ずつ出現
<!-- telop_effect: slide-in -->     # 下からスライド
<!-- telop_effect: bounce -->       # 弾んで出現
<!-- telop_effect: highlight-word --> # 単語ハイライト（静的）
<!-- telop_highlight: 単語1, 単語2 -->
```

## 設計の核心: `t` のみで状態を決定する

アニメーションの状態はシーン内経過秒 `t` のみで決まる純粋関数として実装した。

```python
def _render_bounce(draw, font, text, t, w, h):
    y_offset = int(A * math.exp(-k * t) * math.sin(omega * t + math.pi / 2))
    _draw_bar_and_text(draw, font, text, w, h, y_offset=y_offset)
```

**なぜ `t` のみか:** フレームレンダリングはマルチプロセスで並列実行される。内部カウンタや `time.time()` を使うと同じフレーム番号で異なる値を返す可能性がある。`t` を外から渡すことで「同じ `t` → 同じピクセル」を保証した。

## bounce の位相設計

`sin(omega * t)` のままでは `t=0` がゼロになり、テロップが定位置から始まってしまう。

```python
# NG: t=0 でオフセット0（動きが始まらない）
y_offset = int(A * math.exp(-k * t) * math.sin(omega * t))

# OK: t=0 でオフセット最大（上から落ちてくる動きになる）
y_offset = int(A * math.exp(-k * t) * math.sin(omega * t + math.pi / 2))
```

`+ math.pi / 2` の位相を加えることで `t=0` が `sin(π/2) = 1`（最大値）から始まる「バウンスイン」になる。

## highlight-word の実装順序

テロップ全体を白で描画した後、対象単語の X 範囲を検出して黄色で上書きする。

```python
# 1. 全テキストを通常描画（白文字）
draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

# 2. 対象単語の X 範囲を計算
x_start = x + draw.textlength(line[:idx], font=font)
x_end = x_start + draw.textlength(word, font=font)

# 3. 黄色背景矩形で上書き
draw.rectangle([(x_start, y), (x_end, y + font_size)], fill=(255, 215, 0, 200))

# 4. 黒テキストで単語を再描画（視認性確保）
draw.text((x_start, y), word, font=font, fill=(0, 0, 0, 255))
```

単語単位のマッチは `str.find()` で開始インデックスを求め、`textlength()` で幅を計算する。

## typewriter の pill テロップ（Shorts）での注意点

Shorts の pill テロップは「テキスト幅に合わせて pill サイズが変わる」設計になっている。typewriter で表示文字数が増えると pill が毎フレームガタつく問題が発生した。

**解決策:** pill サイズ計算には全文テキストを使い、描画には表示中テキストを使う。

```python
# pill サイズは全文で計算（ガタつき防止）
size_lines = _wrap_lines(text)  # 全文
pill_w = max(draw.textlength(l, font=font) for l in size_lines) + padding * 2

# 描画は表示中テキスト
draw_lines = _wrap_lines(text[:n_chars])  # 表示中のみ
for line in draw_lines:
    draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
```

## スコープ設計（セクション単位）

`telop_effect` / `telop_highlight` は `telop_hidden` と同じスコープ設計にした。`##` セクション切り替え時にリセットされ、またいで持ち越さない。

```python
# セクション切り替え時にリセット
current_telop_effect = None
current_telop_highlight_words = []
```

BGM はセクションをまたいで持ち越す。`telop_effect` を BGM と同じにしなかった理由は、エフェクトはシーン単位の演出意図を持つことが多く、意図せず後続シーンに引き継がれるほうが問題になりやすいため。

## 不正値の扱い

不正な `telop_effect` 値はパーサー側で `sys.stderr` 警告 + `None` フォールバック（動画生成を止めない）。

```python
if value in VALID_EFFECTS:
    current_telop_effect = TelopEffectConfig(effect=value)
else:
    print(f"警告: 不明な telop_effect 値 '{value}'", file=sys.stderr)
    current_telop_effect = None
```

**なぜ例外にしないか:** 台本ミスで動画生成が失敗すると再生成に28分かかる。不正値はスキップしてデフォルト（フェード）で表示するほうがコストが低い。

## 教訓

- **アニメーションは `t` の純粋関数にする**: マルチプロセス対応とデバッグ容易性が両立する
- **bounce は位相 `π/2` を忘れない**: `sin(0) = 0` のままでは「バウンスイン」にならない
- **pill サイズは全文で計算する**: typewriter でサイズが変わるとガタつく
- **不正値は警告 + スキップ**: 生成コストを考えると例外より寛容な設計が適切
