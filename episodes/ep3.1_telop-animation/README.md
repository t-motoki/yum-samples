# ep3.1 テロップフェードインアニメーション — 静止テロップに「動き」を加える

動画「テロップフェードインアニメーション — 静止テロップに「動き」を加える」のサンプルコードです。

ep3.0 で作った紙芝居パイプラインに、テロップのフェードイン演出を追加した記録です。

## この動画でやること

```
テロップが突然「パン」と出る（before）
  → 0.3秒かけてフワッとフェードインする（after）
```

たった1つの式と、台本への1行追加で実現しています。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `telop_fade_demo.py` | フェードイン計算式の動作確認デモ（Pillow のみで動く） |

---

## セットアップ

```bash
pip install pillow
```

## 使い方

```bash
python telop_fade_demo.py
# → output/ に before.png と after_00.png〜after_09.png が生成される
```

`before.png`（突然出現）と `after_09.png`（フェード完了）を見比べてみてください。

---

## 実装のポイント

### 核心となる式

```python
fade_alpha = min(t / fade_sec, 1.0) if fade_sec > 0 else 1.0
```

| 変数 | 意味 |
| --- | --- |
| `t` | シーン開始からの経過時刻（秒） |
| `fade_sec` | フェードイン完了までの秒数 |
| 戻り値 | `0.0`（透明）〜 `1.0`（完全表示） |

`fade_sec=0` のときは常に `1.0` を返す → アニメーションなし（before の動作）。

### パイプライン内での変更箇所

ep3.0 のパイプラインに対して、変更したのは3箇所だけです。

**① `_draw_telop_bar()` に時刻と秒数を追加**

```python
# before
def _draw_telop_bar(self, frame, scene: Scene) -> None:

# after
def _draw_telop_bar(self, frame, scene: Scene, t: float = 0.0, fade_sec: float = 0.0) -> None:
```

デフォルト値を `0.0` にしているので、既存の呼び出し箇所は変更不要です。

**② フェードイン透明度を計算して描画に反映**

```python
fade_alpha = min(t / fade_sec, 1.0) if fade_sec > 0 else 1.0
# ... テロップバーと文字の描画に fade_alpha を掛ける
```

**③ `MoviePyComposer` を全シーン `VideoClip` に統一**

```python
# before: 静止シーンと動的シーンで分岐していた
if scene.has_animation:
    clip = VideoClip(make_frame, duration=duration)
else:
    clip = ImageClip(frame).set_duration(duration)

# after: テロップがアニメーションする以上、全シーン VideoClip に統一
clip = VideoClip(make_frame, duration=duration)
```

条件分岐が消えてコードがシンプルになりました。

### 台本からフェード秒数を制御する

`<!-- config: telop_fade=normal -->` を台本の先頭に書くだけで制御できます。

| 設定値 | フェード秒数 |
| --- | --- |
| `fast` | 0.1秒 |
| `normal` | 0.3秒 |
| `slow` | 0.8秒 |
| `none` または未記載 | アニメーションなし |
