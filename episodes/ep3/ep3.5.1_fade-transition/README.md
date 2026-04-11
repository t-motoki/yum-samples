# ep3.5.1 シーン間フェードトランジション

動画「シーン間フェードトランジション — 台本1行で全シーンにフェード適用」のサンプルコードです。

## この動画でやること

`<!-- config: transition=fade -->` を台本に1行書くだけで、全シーン間にクロスフェードトランジションが適用される仕組みを実装する。

```
transition なし → シーンが瞬間切り替わる
transition=fade → シーンが自然にフェードで重なる
```

crossfade 適用時に音声がずれるバグの原因と解決策もあわせて解説する。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `fade_transition_demo.py` | クロスフェードトランジションのデモ（赤・緑・青のカラーブロック動画を生成して繋ぐ） |

## セットアップ

```bash
pip install moviepy numpy
```

---

## 使い方

### 基本コマンド

```bash
python fade_transition_demo.py
```

赤 → 緑 → 青 の3シーンをクロスフェードで繋いだ `output.mp4` を生成する。

### パラメータを変えて試す

```bash
# シーンを3秒・フェードを1秒に変える
python fade_transition_demo.py --duration 3 --tr-sec 1.0

# 出力ファイル名を変える
python fade_transition_demo.py --output demo_result.mp4

# フェードを短くしてサクサク切り替える
python fade_transition_demo.py --tr-sec 0.2
```

---

## 実装のポイント

### 1. crossfade の仕組み: CrossFadeIn/Out + padding で映像を重ねる

MoviePy の crossfade は `CrossFadeIn` / `CrossFadeOut` エフェクトと `concatenate_videoclips` の `padding` を組み合わせて実現する。

```python
# 各クリップにフェードエフェクトを付与する
clip = clip.with_effects([CrossFadeIn(tr_sec)])   # 先頭でフェードイン
clip = clip.with_effects([CrossFadeOut(tr_sec)])  # 末尾でフェードアウト

# padding=-tr_sec で隣接クリップを tr_sec 分重ねる
# method="compose" を指定しないと crossfade が効かない
final = concatenate_videoclips(clips, method="compose", padding=-tr_sec)
```

`padding=-0.5` はクリップの開始タイミングを 0.5 秒前に詰めることを意味する。
映像は透明度で合成されるため、フェードアウトとフェードインが重なって自然なトランジションになる。

### 2. 音声タイミングバグと解決策

crossfade で映像を重ねると、**音声も重なってしまう**という問題が起きる。

```
問題の構造:
  クリップA の音声 duration = 2.0 秒
  クリップB の開始 = 1.5 秒後（padding=-0.5 のため）
  → クリップA の音声末尾 0.5 秒にクリップB の音声が重なる
  → シーンが進むたびに音声が前のシーンにずれ込む（累積遅延）
```

解決策は**クリップの duration を `audio.duration + tr_sec` に伸ばして音声末尾に無音バッファを作る**こと。

```python
# 音声は元の duration 分だけ鳴らし、残り tr_sec 分は無音にする
tone = make_tone(frequency, duration)  # duration 秒のトーン

# CompositeAudioClip でラップすると with_duration() が使える
# （ラップしないと set_duration() が音声を繰り返す）
audio_with_buffer = CompositeAudioClip([tone]).with_duration(duration + tr_sec)

# 映像も同じ duration + tr_sec に伸ばす
video = ColorClip(size=size, color=color, duration=duration + tr_sec)
clip = video.with_audio(audio_with_buffer)
```

こうすることで映像が 0.5 秒重なっても、音声はすでに終わっており重ならない。

### 3. 台本1行で全シーンに適用: `<!-- config: transition=fade -->` ディレクティブ

本番の動画生成パイプラインでは、台本に1行書くだけで全シーン間のトランジションが変わる。

```markdown
<!-- config: transition=fade -->
<!-- config: transition-sec=0.5 -->
```

パイプライン内部では以下の処理をすべてのシーン間に適用している:

1. 各シーンクリップの duration を `audio.duration + tr_sec` に伸ばす
2. 音声を `CompositeAudioClip` でラップして無音バッファを付ける
3. `CrossFadeIn` / `CrossFadeOut` エフェクトを付与する
4. `concatenate_videoclips(method="compose", padding=-tr_sec)` で連結する

ディレクティブが1行なのに、内部では4ステップの処理が走っている。
台本作者がこの複雑さを意識しなくてよいのがこの設計の狙い。
