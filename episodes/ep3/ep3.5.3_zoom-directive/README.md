# ep3.5.3 汎用ズーム演出ディレクティブ

動画「zoom ディレクティブ — 任意のシーンに「寄り・引き」をつける」のサンプルコードです。

台本に1行書くだけで任意のシーンにズームイン・ズームアウトを付けられる仕組みを実装しました。

## zoom の動作

```
zoom_in:  clip_t=0 → 1.0x から始まり、duration 秒後に scale 倍に到達
zoom_out: clip_t=0 → scale 倍から始まり、duration 秒後に 1.0x に戻る
```

`clip_t` はクリップ先頭（0.0）からの時刻です。シーンをまたいでもリセットされるため、毎クリップ先頭からアニメーションが始まります。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `zoom_directive_demo.py` | zoom in / zoom out の4パターン（ease_in_out / linear）デモ |

## セットアップ

```bash
pip install Pillow

# 動画（MP4）を出力する場合は imageio も必要
pip install "imageio[ffmpeg]"
```

---

## 使い方

### 1. 代表フレームを PNG として出力

```bash
python zoom_directive_demo.py frames --image avatar.png
```

アニメーション途中（duration/2 秒時点）の4パターンを PNG で出力する。

### 2. 各パターンの動画を MP4 として出力

```bash
python zoom_directive_demo.py video --image avatar.png
```

`zoom_in_ease.mp4` / `zoom_in_linear.mp4` / `zoom_out_ease.mp4` / `zoom_out_linear.mp4` を出力する。

### 3. パラメータを変えて試す

```bash
# 倍率 1.5x・2 秒かけてズーム
python zoom_directive_demo.py video --image avatar.png --scale 1.5 --duration 2.0

# 瞬時切り替え（duration=0）
python zoom_directive_demo.py video --image avatar.png --duration 0

# イージングなし（均等変化）
python zoom_directive_demo.py video --image avatar.png --easing linear
```

---

## 実装のポイント

### calc_zoom_scale: ズーム計算の核心

```python
def calc_zoom_scale(clip_t, direction="in", scale=1.3, duration=1.0, easing="ease_in_out"):
    if duration <= 0.0:
        progress = 1.0
    else:
        raw_progress = min(clip_t / duration, 1.0)
        if easing == "linear":
            progress = raw_progress
        else:
            # ease_in_out: smoothstep（3p^2 - 2p^3）
            p = raw_progress
            progress = 3 * p * p - 2 * p * p * p

    if direction == "in":
        result = 1.0 + (scale - 1.0) * progress
    else:  # "out"
        result = scale - (scale - 1.0) * progress

    return max(1.0, min(result, scale))
```

### なぜ clip_t を使うのか

`scene_elapsed`（シーン開始からの累積時刻）を使うと、「長い発話の後にズームが来る」シーンで
アニメーションが始まらない問題が起きます。

例: セリフが10秒あり、その後の発話でズームしたい場合、`scene_elapsed` は既に10秒を過ぎているため
`min(10.0 / 1.5, 1.0) = 1.0` となり progress=1.0 から始まってしまう（アニメーションが瞬時に終わる）。

`clip_t`（クリップ先頭からの時刻）を使うことで、どのクリップでも t=0 からアニメーションが始まります。

### ease_in_out: smoothstep

```python
progress = 3 * p * p - 2 * p * p * p  # 3p^2 - 2p^3
```

linear と比較:

| 時点 | linear | ease_in_out |
| ---- | ------ | ----------- |
| 0%   | 0.000  | 0.000       |
| 25%  | 0.250  | 0.156       |
| 50%  | 0.500  | 0.500       |
| 75%  | 0.750  | 0.844       |
| 100% | 1.000  | 1.000       |

始まりと終わりが滑らかで、中間が速い S 字曲線。カメラワークに自然な動きを与えます。

### zoom のスコープ

zoom ディレクティブは `##`（セクション）切り替えで自動リセットされます。
また `<!-- expression: -->` や `<!-- speaker: -->` ディレクティブでも即座にリセットされます。

```
# スコープ例

## シーン5                         ← セクション開始
<!-- speaker: yumu -->
ここはズームなし。

<!-- zoom: in scale=1.3 -->        ← ここから zoom 開始
これが zoom in です。              ← zoom あり

<!-- speaker: sabacyan -->         ← speaker 変更 → zoom リセット
あ、本当だ。                       ← さばきゃんはズームなし

## シーン6                         ← セクション切り替え → zoom リセット
次のシーンは等倍に戻る。            ← zoom なし
```

### thinking ズームとの優先順位

thinking 表情には組み込みのズームアクションがあります（`zoom_max_scale` まで緩やかに拡大）。
zoom ディレクティブが存在する場合は thinking の組み込みズームを上書きします。

```python
# pillow_renderer.py の実装イメージ
scale = calc_emotion_offset(emotion, t, scene_elapsed)  # thinking なら緩やかに拡大

if scene.zoom is not None:
    scale = calc_zoom_scale(scene.zoom, clip_t=t)  # zoom ディレクティブで上書き
```

---

## パラメータ一覧

| パラメータ | デフォルト | 意味 |
| --- | --- | --- |
| `scale` | 1.3 | ズーム倍率（1.0 以上） |
| `duration` | 1.0 | アニメーション完了までの秒数（0.0 = 瞬時） |
| `easing` | ease_in_out | イージング関数（`linear` / `ease_in_out`） |
| `direction` | in | 方向（`in` = 拡大 / `out` = 縮小） |
