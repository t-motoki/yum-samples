# ep3.5.4 カメラワーク演出（パン・Ken Burns・画面シェイク）

動画「演出強化 — カメラワーク（パン・Ken Burns・画面シェイク）」のサンプルコードです。

台本に1行書くだけでフレーム全体にカメラワークを付けられる仕組みを実装しました。

## 3つのディレクティブ

```
<!-- pan: right distance=100 duration=2.0 -->
<!-- ken_burns: zoom_start=1.0 zoom_end=1.3 pan_x=40 pan_y=20 duration=3.0 -->
<!-- camera_shake: intensity=medium duration=0.5 -->
```

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `camera_work_demo.py` | pan / ken_burns / camera_shake の全デモ（PNG フレーム出力・MP4 出力） |

## セットアップ

```bash
pip install Pillow

# 動画（MP4）を出力する場合
pip install "imageio[ffmpeg]"
```

---

## 使い方

### 1. 代表フレームを PNG として出力

```bash
python camera_work_demo.py frames --image avatar.png
```

全デモパターン（pan_left/right/up/down・ken_burns・shake_low/medium/high）の
中間フレーム（t = duration/2 秒時点）を PNG で出力する。

### 2. 各パターンの動画を MP4 として出力

```bash
python camera_work_demo.py video --image avatar.png
```

全デモパターンの動画を MP4 で出力する。

### 3. 特定のパターンだけ確認する

```bash
python camera_work_demo.py video --image avatar.png --demo pan_right
python camera_work_demo.py video --image avatar.png --demo ken_burns
python camera_work_demo.py video --image avatar.png --demo shake_high
```

### 4. パラメータを変えて試す

```bash
# pan の移動量を 150px に
python camera_work_demo.py video --image avatar.png --demo pan_left --distance 150

# ken_burns のズーム範囲と duration を変える
python camera_work_demo.py video --image avatar.png --demo ken_burns \
  --zoom-start 1.0 --zoom-end 1.5 --pan-x 60 --pan-y 30 --duration 4.0

# shake の継続時間を長くする
python camera_work_demo.py video --image avatar.png --demo shake_medium --duration 1.5
```

---

## 実装のポイント

### 「拡大してクロップ」でフレームサイズを変えない

pan や camera_shake はカメラ（ビューポート）を動かす演出です。
フレームサイズを変えずにコンテンツを移動させるには、
**少し拡大した画像からクロップする**のが基本パターンです。

```python
# オフセット量に応じて必要な最小 scale を計算する
min_scale_x = 1.0 + abs(total_dx) / w
min_scale_y = 1.0 + abs(total_dy) / h
effective_scale = max(scale, min_scale_x, min_scale_y)

# 拡大 → クロップ
enlarged = frame.resize((int(w * effective_scale), int(h * effective_scale)))
left = center_x + total_dx   # 中央基準でオフセットを加算
top  = center_y + total_dy
return enlarged.crop((left, top, left + w, top + h))
```

scale=1.0 の pan や shake でも同じパイプラインを通るため、処理が統一されます。

### ken_burns: ズームとパンを同一 progress で動かす

```python
p = _progress(scene_elapsed, duration, easing)
scale = zoom_start + (zoom_end - zoom_start) * p   # ズーム
dx    = int(pan_x * p)                              # X パン
dy    = int(pan_y * p)                              # Y パン
```

zoom と pan を別々の関数で動かすと動きがバラバラになります。
同一の `progress` を使うことで、ズームとパンが同じリズムで変化します。

### camera_shake の elapsed を分離する理由

pan / ken_burns はセクション先頭からの累積時刻（`scene_elapsed`）でアニメーションが進みます。

camera_shake に同じ値を渡すと、**2クリップ目以降でシェイクが無効**になります:

```
シーン: 0秒 ─── 発話クリップA（3秒） ─── 発話クリップB（2秒）
                                     ↑ clip_B の先頭で scene_elapsed = 3.0

camera_shake duration=0.5 の場合:
  scene_elapsed=3.0 > duration=0.5 → シェイク終了と判定されてしまう
```

対策として、**シェイク開始クリップの先頭を 0 とした別の elapsed**（`shake_elapsed`）を管理します:

```python
shake_elapsed = camera_shake_elapsed_before + t
# camera_shake_elapsed_before: シェイク開始クリップの先頭 = 0 に固定
```

### ease_in_out: smoothstep

```python
def _smoothstep(p: float) -> float:
    return 3 * p * p - 2 * p * p * p  # 3p^2 - 2p^3
```

| 時点 | linear | ease_in_out |
| ---- | ------ | ----------- |
| 0%   | 0.000  | 0.000       |
| 25%  | 0.250  | 0.156       |
| 50%  | 0.500  | 0.500       |
| 75%  | 0.750  | 0.844       |
| 100% | 1.000  | 1.000       |

始まりと終わりが滑らかで、中間が速い S 字曲線。カメラワークに自然な動きを与えます。

### camera_shake の「ランダムに見える揺れ」

```python
# X: 13Hz / Y: 17Hz（非整数比率でランダムに見える揺れを作る）
dx = int(amp * math.sin(2 * math.pi * 13.0 * elapsed))
dy = int(amp * math.sin(2 * math.pi * 17.0 * elapsed))
```

1つのサイン波だと単純な往復になります。
X と Y で非整数比率の周波数（13 / 17）を使うことで、リサージュ図形的な軌跡となり
「ランダムに見える揺れ」を表現できます。
決定論的（同じ elapsed → 同じオフセット）なので再現性も保証されます。

---

## パラメータ一覧

### pan

| パラメータ | デフォルト | 意味 |
| --- | --- | --- |
| `direction` | （必須） | `left` / `right` / `up` / `down` |
| `distance` | 100 | 移動量 px |
| `duration` | 1.0 | アニメーション完了までの秒数 |
| `easing` | ease_in_out | `linear` / `ease_in_out` |

### ken_burns

| パラメータ | デフォルト | 意味 |
| --- | --- | --- |
| `zoom_start` | 1.0 | 開始倍率 |
| `zoom_end` | 1.3 | 終了倍率 |
| `pan_x` | 0 | X 方向パン量 px（正 = 右） |
| `pan_y` | 0 | Y 方向パン量 px（正 = 下） |
| `duration` | 1.0 | アニメーション完了までの秒数 |
| `easing` | ease_in_out | `linear` / `ease_in_out` |

### camera_shake

| パラメータ | デフォルト | 意味 |
| --- | --- | --- |
| `intensity` | medium | `low`(4px) / `medium`(8px) / `high`(16px) |
| `duration` | 0.5 | シェイク継続秒数 |
