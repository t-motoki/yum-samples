# ep3.4.3 表情補間 + アイドルアニメーション

動画「口だけ動いて体が固まる問題 — 表情補間とアイドルアニメーションで人形感を解消する」のサンプルコードです。

## この動画でやること

口パクで動くようになったキャラクターに残る「人形感」を2つの手法で解消する。

```
【表情補間】
口を閉じた絵 → (瞬間カット) → 口を開いた絵   ← パッと切り替わる（人形っぽい）
口を閉じた絵 → (数フレームで blend) → 口を開いた絵  ← なめらかに変わる
```

```
【アイドルアニメーション】
キャラクターの Y 座標 += A × sin(2π × f × t)  ← 一定のリズムで上下に揺れる
amplitude=6px、frequency=0.4Hz（2.5秒に1往復）がデフォルト
```

どちらも **Pillow だけ**で実装できる。外部ライブラリの追加は不要。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `blend_idle_demo.py` | 表情補間・アイドルアニメーションのデモ（PNG / MP4 生成） |

## セットアップ

```bash
pip install Pillow

# アイドルアニメーション動画を生成する場合は imageio も必要
pip install "imageio[ffmpeg]"
```

追加ライブラリはこれだけ。GPU は不要。

---

## 使い方

### 1. 表情補間の比較フレームを生成

```bash
python blend_idle_demo.py blend --normal normal.png --open lipsync_open.png
```

- `blend_before.png` … blend なし（瞬間カット）
- `blend_after.png`  … blend あり（3フレーム補間の中間フレーム）

補間フレーム数を変えるには `--frames` を使う:

```bash
python blend_idle_demo.py blend --normal normal.png --open lipsync_open.png --frames 6
```

### 2. アイドルアニメーション動画を生成

```bash
python blend_idle_demo.py idle --image normal.png
```

デフォルト設定（3秒・30fps・amplitude=6px・frequency=0.4Hz）で `idle_demo.mp4` を出力する。

振れ幅・周波数を変えるには:

```bash
# より大きく揺らす（amplitude=12px）
python blend_idle_demo.py idle --image normal.png --amplitude 12

# より速く揺らす（frequency=1.0Hz = 1秒に1往復）
python blend_idle_demo.py idle --image normal.png --frequency 1.0
```

### 3. 両方まとめて生成

```bash
python blend_idle_demo.py all --normal normal.png --open lipsync_open.png
```

---

## 実装のポイント

### 表情補間: Image.blend() で数フレームかけて遷移させる

```python
from PIL import Image

def blend_expressions(prev_img, curr_img, alpha: float):
    return Image.blend(prev_img, curr_img, alpha)
```

`alpha` を 0→1 に徐々に変化させることで、表情の切り替えをなめらかに見せる。

```
フレーム 0: alpha=0.0  → prev_img（口を閉じた状態）
フレーム 1: alpha=0.33 → 前後の中間（ぼんやりした状態）
フレーム 2: alpha=0.67 → 後の絵に近い状態
フレーム 3: alpha=1.0  → curr_img（口を開いた状態）
```

**blend を適用するのは lipsync 表情間のみ**。
笑顔・驚きなど「意図的な表情変化」には blend を適用しない。
理由: キャラクターの演技の切れ目をぼかしてしまうため。

### アイドルアニメーション: 正弦波で Y 座標をオフセットする

```python
import math

def calc_idle_offset_y(t: float, amplitude=6.0, frequency=0.4) -> int:
    return int(amplitude * math.sin(2 * math.pi * frequency * t))
```

`t` に現在時刻（秒）を渡すだけ。Python 標準の `math` だけで動く。

Y 座標への適用:

```python
offset_y = calc_idle_offset_y(t)
idle_margin = int(amplitude)  # 上スイング時の画面外クリッピングを防ぐシフト量
y = base_y + offset_y + idle_margin
```

`idle_margin` のポイント: `offset_y` の最小値は `-amplitude`（sin が -1 のとき）。
`idle_margin = amplitude` を足すことで、上スイング最大でも `y = base_y + 0` になり
キャラクターが画面外に出ない。

### パラメータの意味

| パラメータ | デフォルト | 意味 |
| --- | --- | --- |
| `blend_frames` | 3 | 補間に使うフレーム数。30fps で約 0.1秒の遷移 |
| `amplitude` | 6.0 | 揺れ振幅（px）。大きくするほどよく揺れる |
| `frequency` | 0.4 | 揺れ周波数（Hz）。0.4Hz = 2.5秒で1往復 |

---

## 口パクとの組み合わせ

このサンプルは表情補間・アイドルアニメーション単体のデモです。
口パク（Rhubarb Lip Sync）と組み合わせた実装については ep3.4.2 のサンプルを参照してください。

```
ep3.4.2_rhubarb-lipsync/rhubarb_demo.py  ← 口パクのタイミングデータを取得する
ep3.4.3_expression-blend-idle/blend_idle_demo.py  ← 表情補間・揺れを加える
```

この2つを組み合わせると「音声に合わせて口が動き、なめらかに表情が変わり、体が揺れる」キャラクター動画ができます。
