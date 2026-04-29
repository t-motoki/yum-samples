# カメラワークディレクティブの設計: 拡大クロップ・elapsed 分離・shake の非整数比率

## 問題

「フレーム全体を動かす」演出（パン・Ken Burns・画面シェイク）を台本から制御したい。
しかし MoviePy のクリップは固定サイズで出力されるため、
「カメラを動かす＝フレームサイズを変えずにコンテンツを移動させる」必要がある。

加えて、複数クリップにまたがるシーンでは、2クリップ目以降で演出が途切れるバグが起きやすい。

---

## 設計の核心

### 1. 「拡大してクロップ」でフレームサイズ不変のまま移動する

pan や shake は「カメラが動いて中のコンテンツが相対移動して見える」演出。
実装するには **フレームより少し大きな画像からクロップする** のが基本パターン。

```python
# オフセット量に応じた最小 scale を確保する
min_scale_x = 1.0 + abs(total_dx) / w
min_scale_y = 1.0 + abs(total_dy) / h
effective_scale = max(scale, min_scale_x, min_scale_y)

enlarged = frame.resize((int(w * effective_scale), int(h * effective_scale)))
left = center_x + total_dx
top  = center_y + total_dy
return enlarged.crop((left, top, left + w, top + h))
```

pan だけなら scale=1.0 でも動作する（オフセット分だけ拡大）。
ken_burns（zoom + pan 同時）の場合は zoom の scale が min_scale を上回るので自動的に大きくなる。
すべての演出が「拡大 → クロップ」の同一パイプラインを通るため処理が統一できる。

### 2. pan / ken_burns と camera_shake で elapsed を分離する

pan / ken_burns はセクション先頭からの累積時刻（`scene_elapsed`）でアニメーションが進む。
これにより「セクション内で複数クリップにまたがってもパンが継続する」。

camera_shake に同じ elapsed を渡すと問題が起きる:

```
シーン: 0秒 ─── クリップA（3秒） ─── クリップB（2秒）
                                  ↑ クリップB 先頭: scene_elapsed = 3.0

camera_shake duration=0.5 の場合:
  scene_elapsed=3.0 > 0.5 → 「シェイク終了」と判定されてしまう
```

対策: **シェイク開始クリップの先頭を 0 とした別の elapsed**（`shake_elapsed`）を管理する。

```python
# クリップ開始時に shake_elapsed_before を計算して Scene に埋め込む
# - camera_shake が始まるクリップの先頭: shake_elapsed_before = 0
# - 以降のクリップ: shake_elapsed_before += 前クリップの duration
shake_elapsed = scene.camera_shake_elapsed_before + t
```

pan / ken_burns はセクションをまたいで継続させたい（長い発話でもパンを続ける）。
camera_shake は短時間の「瞬間的な揺れ」なのでクリップをまたぐことはほぼない。
この違いが elapsed を分離する設計理由になっている。

### 3. ken_burns: ズームとパンを同一 progress で補間する

```python
p = smoothstep(scene_elapsed / duration)   # 同一の progress
scale = zoom_start + (zoom_end - zoom_start) * p
dx    = int(pan_x * p)
dy    = int(pan_y * p)
```

zoom と pan を別々の関数で動かすと「ズームは速く始まってパンは遅い」ような不自然な動きになる。
同一 progress を使うことで、カメラの移動が一体感のある動きに見える。

### 4. camera_shake の「ランダムに見える揺れ」: 非整数比率の周波数

```python
# X: 13Hz / Y: 17Hz（13:17 は非整数比率）
dx = int(amp * math.sin(2 * math.pi * 13.0 * elapsed))
dy = int(amp * math.sin(2 * math.pi * 17.0 * elapsed))
```

1本のサイン波では単純な往復になる。
X/Y で **非整数比率の周波数** を使うことでリサージュ図形的な軌跡になり、
「ランダムに見える自然な揺れ」を乱数なしで実現できる。

決定論的（同じ elapsed → 同じオフセット）なので、
動画生成を繰り返しても同じ結果になる（再現性の保証）。

---

## 実装上の教訓

### telop_mode: "fixed" vs "float"

テロップ（字幕バー）をカメラワーク前に描画するか後に描画するかで見え方が変わる。

- `fixed`（デフォルト）: カメラワーク後にテロップを上書き → テロップは画面固定で動かない
- `float`: カメラワーク前にテロップを描画 → テロップがカメラと一緒に動く

通常は `fixed` が自然（テロップが揺れると読みにくい）。
クリップ埋め込みや特殊演出では `float` が必要になることがある。

### セクション境界でのリセット

pan / ken_burns / camera_shake はすべて `##` セクション切り替えで自動リセットされる。
「ディレクティブが次のシーンに引き継がれる」と演出がずっと続いてしまうため、
セクション境界でリセットするのが自然なスコープ設計になっている。

同じ設計パターンは zoom ディレクティブ（ep3.5.3）や telop_hidden でも採用している。

---

## 教訓

- 「フレームサイズを変えずに移動させる」→ 拡大クロップのパターンを覚える
- 「クリップをまたぐアニメーション」→ elapsed を事前計算して Scene に埋め込む
- 「瞬間演出 vs 継続演出」→ elapsed の起点を分ける（shake と pan で別管理）
- 「ランダムに見せる」→ 乱数でなく非整数比率の周波数で決定論的に再現
