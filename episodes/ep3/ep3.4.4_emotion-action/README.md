# ep3.4.4 感情連動アニメーション（Emotion-Driven Action）

動画「感情ラベルが体を動かす — joy で弾んで、surprise で揺れる仕組み」のサンプルコードです。

## この動画でやること

感情ラベル（joy / surprise / thinking / normal）に応じてアバターの体の動きが変わる仕組みを実装する。

```
joy      → bounce:   アイドルの2倍の振幅・周波数で上下に弾む
surprise → shake:    フレームごとにランダムで左右に横揺れ
thinking → zoom_in:  シーン経過時間に応じて最大1.1倍まで線形に拡大
normal   → idle のみ（常時ゆらゆら揺れるだけ）
```

追加ライブラリはゼロ。**Pillow と標準ライブラリ（math・random）だけ**で動く。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `emotion_action_demo.py` | 感情連動アニメーションのデモ（PNG / MP4 生成） |

## セットアップ

```bash
pip install Pillow

# 動画（MP4）を出力する場合は imageio も必要
pip install "imageio[ffmpeg]"
```

---

## 使い方

### 1. 各感情の代表フレームを PNG として出力

```bash
python emotion_action_demo.py frames --image avatar.png
```

`emotion_normal.png` / `emotion_joy.png` / `emotion_surprise.png` / `emotion_thinking.png` を出力する。

### 2. 各感情の動画を MP4 として出力

```bash
python emotion_action_demo.py video --image avatar.png
```

感情ごとに3秒・30fps の `emotion_<名前>.mp4` を出力する。

### 3. パラメータを変えて試す

```bash
# joy の振れ幅を3倍にする
python emotion_action_demo.py video --image avatar.png --joy-amplitude 3.0

# surprise の横揺れを大きくする
python emotion_action_demo.py video --image avatar.png --surprise-amplitude 8

# thinking のズームを遅くする（5秒かけてフルスケール）
python emotion_action_demo.py video --image avatar.png --zoom-duration 5.0
```

---

## 実装のポイント

### 核心: `calc_emotion_offset()` で感情→オフセットを決める

```python
def calc_emotion_offset(emotion, t, scene_elapsed=0.0, ...) -> tuple[int, int, float]:
    # 返り値: (offset_x, offset_y, scale)
```

感情ラベルと現在時刻を受け取って `(offset_x, offset_y, scale)` の3値を返すだけ。
呼び出し元の描画ループは感情の種類を知らなくてよい。

### joy: アイドルと同じ sin 波・振れ幅だけ2倍

```python
if emotion == "joy":
    joy_amplitude = idle_amplitude * joy_amplitude_ratio  # 2倍
    joy_frequency = idle_frequency * joy_frequency_ratio  # 2倍
    offset_y = int(joy_amplitude * math.sin(2 * math.pi * joy_frequency * t))
    return (0, offset_y, 1.0)
```

**新しい計算式はゼロ。** ep3.4.3 のアイドルアニメーションと同じ sin 波を使い、
振れ幅と周波数を変えるだけで「弾んでいる」感じを出している。

### surprise: ランダム左右揺れ（ちらつき）

```python
elif emotion == "surprise":
    offset_x = random.choice([-amp, amp]) if amp != 0 else 0
    return (offset_x, 0, 1.0)
```

フレームごとに `-amp` か `+amp` をランダムに選ぶ。
このランダムなちらつきが「驚いて体が震える」感じを演出する。

### thinking: 線形 zoom_in

```python
elif emotion == "thinking":
    progress = min(scene_elapsed / zoom_duration_sec, 1.0)
    scale = 1.0 + (zoom_max_scale - 1.0) * progress  # 1.0 → 1.1 に線形増加
    return (0, 0, scale)
```

`scene_elapsed`（シーン開始からの経過秒数）を使って、
シーンが始まるたびに zoom が最初からやり直される。

### joy と他の感情の合算ルールの違い

```
joy の場合    : bounce のみ（アイドルは止める）← 上下が二重になって不自然になるため
その他の場合  : アイドル + 感情オフセットを加算 ← 方向が干渉しないので加算でOK
```

surprise（横）と normal idle（縦）は方向が違うので加算しても自然に見える。
joy（縦上下）と idle（縦上下）は同じ方向なので重なると動きすぎる。

---

## パラメータの意味

| パラメータ | デフォルト | 意味 |
| --- | --- | --- |
| `idle_amplitude` | 6.0 | アイドル揺れ振幅（px） |
| `idle_frequency` | 0.4 | アイドル揺れ周波数（Hz）。0.4Hz = 2.5秒で1往復 |
| `joy_amplitude_ratio` | 2.0 | joy 振幅 = idle_amplitude × ratio |
| `joy_frequency_ratio` | 2.0 | joy 周波数 = idle_frequency × ratio |
| `surprise_shake_amplitude` | 3 | surprise の横揺れ幅（px）|
| `zoom_duration_sec` | 2.0 | thinking がフルスケールに達するまでの秒数 |
| `zoom_max_scale` | 1.1 | thinking の最大拡大率（1.0 = 等倍）|

---

## ep3.4.3 との関係

このサンプルは ep3.4.3（表情補間 + アイドルアニメーション）の続きです。

```
ep3.4.3_expression-blend-idle/blend_idle_demo.py  ← アイドルアニメーション（sin 波の基礎）
ep3.4.4_emotion-action/emotion_action_demo.py     ← 感情ラベルで動きを変える（sin 波の流用）
```

ep3.4.3 で作ったアイドルの「sin 波」を、ep3.4.4 でそのまま joy の bounce に流用している。
