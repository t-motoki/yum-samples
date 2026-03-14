# 動画生成の高速化 — 27分から10分以内へ

動画生成パイプラインが ep3.1 のテロップアニメーション実装後に 27分55秒 かかるようになった問題と、その解決方法を記録します。

## 問題

ep3.1 でテロップフェードインアニメーションを実装した際、全シーンを `VideoClip` に統一した。
その結果、アニメーションのないシーンでも毎フレーム `render()` が呼ばれるようになり、
短〜中尺の動画でも生成に 27分以上 かかるようになった。

```text
非機能要件: 動画生成は 10分以内
実測値:     27分55秒（ep3.1 実装直後）
```

## 原因分析

MoviePy には2種類のクリップがある。

| クリップ種別 | 動作 | 処理コスト |
| --- | --- | --- |
| `ImageClip` | 静止画として保持。フレームを毎回生成しない | 低 |
| `VideoClip` | フレーム生成関数を毎フレーム呼び出す | 高 |

ep3.1 以前は「アニメーションあり → `VideoClip`、なし → `ImageClip`」と分岐していたが、
テロップフェードを実装する際にすべて `VideoClip` に統一してしまった。

```python
# before: 分岐あり（高速）
if scene.has_animation:
    clip = VideoClip(make_frame, duration=duration)
else:
    clip = ImageClip(frame).set_duration(duration)

# after（問題のある実装）: 全シーン VideoClip（低速）
clip = VideoClip(make_frame, duration=duration)
```

## 解決策

`fade_sec == 0.0` のシーンは `ImageClip` にフォールバックする条件分岐を復活させた。

```python
if fade_sec > 0:
    # テロップフェードあり → 毎フレーム描画が必要
    clip = VideoClip(make_frame, duration=duration)
else:
    # テロップフェードなし → 静止画で十分
    frame = render_static_frame(scene)
    clip = ImageClip(frame).with_duration(duration)
```

ポイントは「`fade_sec > 0` かどうか」だけで判断できること。
台本で `<!-- config: telop_fade=none -->` または未設定のシーンはすべて `ImageClip` になる。

## 結果

| 条件 | 生成時間 |
| --- | --- |
| 修正前（全シーン VideoClip） | 約28分 |
| 修正後（フォールバックあり） | 短〜中尺は10分以内 |
| 長尺動画 | 依然10分超過（未解決） |

短〜中尺動画（〜10シーン程度）は非機能要件（10分以内）を達成。
長尺動画については並列レンダリングなどの追加対応が必要（未着手）。

## 教訓

- `ImageClip` と `VideoClip` の使い分けは MoviePy のパフォーマンスに直結する
- 「全部 VideoClip にしておけば安全」はアンチパターン
- アニメーション実装時は必ず「アニメーションなしのシーンへの影響」を確認する
- 処理時間の非機能要件を先に決めておくと、実装の方針が明確になる
