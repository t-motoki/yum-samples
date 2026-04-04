# idle animation がシーン境界でリセットされる問題

## 問題

キャラクターの idle アニメーション（ふわふわ揺れ）がシーンをまたぐたびに
sin(0) にリセットされ、速く見えたり不自然な跳びが発生する。

```
シーン1: t=0〜2秒 → sin(0) から始まる（上から下へ）
シーン2: t=0〜2秒 → また sin(0) から始まる（また上から下へ）
シーン3: t=0〜2秒 → また sin(0) から始まる（ループ感が出る）
```

同じ動きが毎シーン繰り返されるためリズムが単調になり、
「速すぎる」「ぴこぴこしている」と感じられた。

## 原因

アニメーション計算に MoviePy のクリップ相対時刻 `t`（シーン先頭で毎回 0 にリセット）を使っていた。

```python
# 修正前（バグあり）
idle_offset = self._calc_idle_offset_y(t)  # t = 0 from each clip start
```

MoviePy の `make_frame(t)` に渡される `t` は各クリップの先頭を 0 とした相対時刻のため、
クリップが変わるたびに t=0 から再開する。

## 解決策

`scene_elapsed = prior_elapsed + t` を使う。

`prior_elapsed` はそのシーンが始まる前に経過した累積時間。これにシーン内の `t` を足すと、
「動画の先頭からの通算時刻」に近い値になり、シーン境界をまたいでも連続した揺れになる。

```python
# 修正後
prior_elapsed = scene.expression_elapsed_before.get(char_name, 0.0)
scene_elapsed = prior_elapsed + t
idle_offset = self._calc_idle_offset_y(scene_elapsed)  # クリップをまたいでも連続
```

周波数も 0.33Hz（3秒で1往復）に設定することで「ゆったりした揺れ」を実現した。

## clip_t vs scene_elapsed の使い分け

既存の Note（[clip-relative-time-vs-scene-elapsed.md](clip-relative-time-vs-scene-elapsed.md)）とは逆のケース。

| アニメーション | 使う時刻 | 理由 |
|--------------|---------|------|
| zoom in/out | `clip_t`（クリップ相対） | クリップごとに t=0 から始めたい |
| idle 揺れ | `scene_elapsed`（シーン累積） | シーンをまたいで連続した揺れにしたい |
| sad 沈下 | `scene_elapsed`（シーン累積） | 沈み続ける演出を保持したい |
| chibi bounce | `scene_elapsed`（シーン累積） | ← 今回修正。従来は clip_t を使っていた |

「リセットされてほしくない」アニメーションには `scene_elapsed`、
「毎シーン新鮮に始まってほしい」アニメーションには `clip_t` を使う。

## 教訓

- アニメーションを実装するとき「シーン切り替えでリセットされてよいか？」を最初に確認する
- 「速すぎる」という視覚的フィードバックは「シーン境界でリセットされているサイン」のことがある
- chibi の bounce のような「常時かかるアニメーション」は特に `scene_elapsed` が適切
