# ep3.5.2 感情アクション拡張（5種追加）

動画「怒ると揺れて、悲しむと沈む — 感情ごとに動きが変わる仕組みを作った」のサンプルコードです。

ep3.4.4 の3種（joy / surprise / thinking）に加えて、新たに5種類の感情アクションを追加した完全版です。

## 感情アクション一覧（全9種）

```
【ep3.4.4 から引き継ぎ】
joy      → bounce:    アイドルの2倍の振幅・周波数で上下に弾む
surprise → shake:     フレームごとにランダムで左右に横揺れ
thinking → zoom_in:   scene_elapsed に応じて最大 1.1 倍まで線形に拡大

【ep3.5.2 で追加】
angry    → 激しい横揺れ: surprise の2倍以上の振れ幅・速い周期（±8px）
sad      → ゆっくり沈む: scene_elapsed に比例して Y 下方向に移動（最大 20px）
smile    → 穏やかな縦揺れ: joy と同系だが振れ幅・周波数を抑えた落ち着いたバウンス
troubled → 小刻みな縦揺れ: 小さい振幅（4px）・速い周期（2Hz）の上下揺れ
chibi    → 素早いバウンス: joy より高周波（3Hz）・小振幅の上下バウンス
normal   → idle のみ（常時ゆらゆら揺れるだけ）
```

追加ライブラリはゼロ。**Pillow と標準ライブラリ（math・random）だけ**で動く。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `emotion_action_demo_v2.py` | 感情アクション9種のデモ（PNG / MP4 生成） |

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
python emotion_action_demo_v2.py frames --image avatar.png
```

`emotion_normal.png` / `emotion_joy.png` / ... / `emotion_chibi.png` の9ファイルを出力する。

### 2. 各感情の動画を MP4 として出力

```bash
python emotion_action_demo_v2.py video --image avatar.png
```

感情ごとに3秒・30fps の `emotion_<名前>.mp4` を出力する。

### 3. パラメータを変えて試す

```bash
# angry をより激しく
python emotion_action_demo_v2.py video --image avatar.png --angry-amplitude 12

# sad がゆっくり沈むようにする（5秒かけてフルに沈む）
python emotion_action_demo_v2.py video --image avatar.png --sad-duration 5.0

# chibi の弾みを速くする
python emotion_action_demo_v2.py video --image avatar.png --chibi-frequency 5.0
```

---

## 実装のポイント

### 感情アクションの設計思想

**感情を物理的な動きに翻訳する**。「怒り」は激しさ、「悲しみ」は重力、「安心」はゆったりした揺れ——感情の性質に合った「物理的な比喩」を動きに落とし込む。

### 加算か置き換えか

感情アクションとアイドルアニメーション（常時の縦揺れ）の合算ルールは感情によって異なる。

```
joy / smile の場合 : bounce のみ（アイドルは止める）
その他の場合      : アイドル + 感情オフセットを加算
```

joy・smile は縦方向の揺れで、アイドルも縦方向。そのまま加算すると振れ幅が2倍になって不自然に見える。
angry（横）・troubled（縦・小振幅）・chibi（縦・小振幅）はアイドルと方向が違うか振れ幅が小さいため加算しても自然に見える。

### angry vs surprise: 同じ横揺れ系でも設計が別物

```python
# surprise: ±3px、フレームごとのランダム
offset_x = random.choice([-3, 3])

# angry: ±8px（2.5倍以上）、同じランダム
offset_x = random.choice([-8, 8])
```

振れ幅だけ変えることで「驚き」と「怒り」の激しさの差を出している。

### sad: 時間経過で変化する唯一の感情

```python
elapsed = max(scene_elapsed, 0.0)
sink = (elapsed / sad_sink_duration_sec) * sad_sink_max_px
wave = sad_wave_amplitude * math.sin(2 * math.pi * sad_wave_frequency * elapsed)
total_dy = min(sink + wave, sad_sink_max_px)
```

`scene_elapsed`（シーン開始からの経過秒数）を使って時間とともに沈んでいく。
微小なサイン波（wave）を重畳してよろめきを表現。最大値（`sad_sink_max_px`）でクランプして画面外に出ない。

### troubled vs chibi: 同じ縦揺れ・周波数で差別化

| 感情 | 振れ幅 | 周波数 | 印象 |
| --- | --- | --- | --- |
| troubled | 4px | 2.0Hz | 細かく震える・不安感 |
| chibi | 5px | 3.0Hz | より速く弾む・かわいらしさ |

周波数の差（2.0Hz vs 3.0Hz）が「おろおろしている」と「はしゃいでいる」の違いを生む。

---

## パラメータ一覧

| パラメータ | デフォルト | 意味 |
| --- | --- | --- |
| `idle_amplitude` | 6.0 | アイドル振れ幅（px） |
| `idle_frequency` | 0.4 | アイドル周波数（Hz） |
| `joy_amplitude_ratio` | 2.0 | joy 振幅 = idle_amplitude × ratio |
| `joy_frequency_ratio` | 2.0 | joy 周波数 = idle_frequency × ratio |
| `smile_amplitude_ratio` | 1.0 | smile 振幅 = idle_amplitude × ratio |
| `smile_frequency_ratio` | 1.0 | smile 周波数 = idle_frequency × ratio |
| `surprise_shake_amplitude` | 3 | surprise の横揺れ幅（px） |
| `angry_shake_amplitude` | 8 | angry の横揺れ幅（px） |
| `sad_sink_max_px` | 20 | sad の最大沈み量（px） |
| `sad_sink_duration_sec` | 3.0 | sad がフルに沈むまでの秒数 |
| `sad_wave_amplitude` | 2 | sad のよろめき波 振れ幅（px） |
| `sad_wave_frequency` | 0.5 | sad のよろめき波 周波数（Hz） |
| `troubled_amplitude` | 4 | troubled の振れ幅（px） |
| `troubled_frequency` | 2.0 | troubled の周波数（Hz） |
| `chibi_amplitude` | 5 | chibi の振れ幅（px） |
| `chibi_frequency` | 3.0 | chibi の周波数（Hz） |
| `zoom_duration_sec` | 2.0 | thinking がフルスケールに達するまでの秒数 |
| `zoom_max_scale` | 1.1 | thinking の最大拡大率 |

---

## ep3.4.4 との関係

このサンプルは ep3.4.4（感情連動アニメーション）の拡張版です。

```
ep3.4.4_emotion-action/emotion_action_demo.py    ← 3種（joy / surprise / thinking）
ep3.5.2_emotion-actions-extended/emotion_action_demo_v2.py  ← 9種（+angry/sad/smile/troubled/chibi）
```

設計の骨格（`calc_emotion_offset()` が `(dx, dy, scale)` を返す構造）は ep3.4.4 から変わらない。
新しい感情は既存の `elif` チェーンに追加するだけで拡張できる。
