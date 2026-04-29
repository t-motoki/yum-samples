# MoviePy の ImageClip と VideoClip — パフォーマンスに直結する使い分け

MoviePy で動画を生成するとき、`ImageClip` と `VideoClip` のどちらを使うかで
処理時間が大きく変わります。

## 2つのクリップの違い

| クリップ種別 | 動作 | 処理コスト |
| --- | --- | --- |
| `ImageClip` | 静止画を1枚保持。フレームを毎回生成しない | 低 |
| `VideoClip` | フレーム生成関数を **毎フレーム** 呼び出す | 高 |

```python
from moviepy import ImageClip, VideoClip

# ImageClip: 静止画をそのまま使う
clip = ImageClip(frame_ndarray).with_duration(duration)

# VideoClip: フレームごとに関数を呼び出す
def make_frame(t):
    return render_frame_at_time(t)  # 毎フレーム呼ばれる

clip = VideoClip(make_frame, duration=duration)
```

## アニメーションが不要なシーンには ImageClip を使う

30fps・10秒のシーンでは `VideoClip` は `make_frame` を **300回** 呼び出す。
静止画のシーンであれば `ImageClip` で1回のレンダリングで済む。

```python
# ❌ アニメーションなしのシーンに VideoClip を使う（遅い）
clip = VideoClip(lambda t: static_frame, duration=duration)

# ✅ アニメーションなしのシーンは ImageClip を使う（速い）
clip = ImageClip(static_frame).with_duration(duration)
```

## 条件分岐で使い分けるパターン

```python
def make_clip(scene, duration: float):
    if scene.has_animation:
        # フェードイン・アニメーションなど時間変化があるシーン
        def make_frame(t):
            return render_animated_frame(scene, t)
        return VideoClip(make_frame, duration=duration)
    else:
        # 静止画のシーン
        frame = render_static_frame(scene)
        return ImageClip(frame).with_duration(duration)
```

「アニメーションあり → `VideoClip`、なし → `ImageClip`」のルールを守るだけで
全体の処理時間が大幅に改善する。

## 実測値（参考）

| 条件 | 生成時間（10シーン・合計60秒） |
| --- | --- |
| 全シーン VideoClip | 約28分 |
| 静止シーンを ImageClip にフォールバック | 約6〜8分 |

シーンの大半が静止画の動画では 3〜4倍の差が出る。

## テロップフェードアニメーションとの関係

テロップがフェードインするシーンは必ず `VideoClip` が必要（時刻 `t` に応じて透明度が変わる）。
テロップフェードなし（`fade_sec=0`）のシーンだけ `ImageClip` にフォールバックすれば十分。

```python
if fade_sec > 0:
    clip = VideoClip(make_frame, duration=duration)
else:
    frame = render_static_frame(scene)
    clip = ImageClip(frame).with_duration(duration)
```

## まとめ

- `VideoClip` は「アニメーションが必要なシーン」だけに使う
- 静止画シーンに `VideoClip` を使うのはアンチパターン
- アニメーション追加時は「アニメーションなしのシーンへの影響」を必ず確認する
