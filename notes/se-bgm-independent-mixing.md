# SE と BGM を独立したフローで処理する設計

## 問題

SE（効果音）を BGM と同じミックスフローで処理しようとすると、
「BGM を少し下げたら SE のタイミングもずれた」「SE の音量が BGM 設定に引きずられた」
という干渉問題が起きる。

SE と BGM はそれぞれ独立した演出目的を持つ：

| | SE | BGM |
|---|---|---|
| 目的 | 特定のセリフ・場面への瞬間的な強調 | 動画全体の雰囲気・感情の底支え |
| タイミング | シーン内の任意の秒数（offset） | 動画全体・フェードイン/アウト |
| 音量調整 | SE ファイル自体の音量が基準 | BGM 全体に volumeScale をかける |

これらを同一フローで処理すると、一方の調整がもう一方に影響する。

## 解決策: 2層ミックス設計

SE と BGM を別のミックスフローに分離する。

```
ナレーション音声 (WAV)
    │
    ▼
CompositeAudioClip([narration, se_audio.with_start(offset)])
    │  ← シーンクリップ内で SE を焼き込む
    ▼
シーン MP4（SE 込みの音声が埋め込まれた状態）
    │
    ▼
ffmpeg amix（BGM を重ねる）
    │  ← 最終出力で BGM を混ぜる
    ▼
最終動画 MP4
```

### SE ミックス（シーンクリップレベル）

```python
# _build_se_tracks: SECue リストから with_start 済み AudioFileClip を生成
def _build_se_tracks(se_cues, resolver):
    tracks = []
    for cue in se_cues:
        path = resolver.resolve(cue.preset)
        if path is None:
            continue
        se_audio = AudioFileClip(str(path)).with_start(cue.offset)
        tracks.append(se_audio)
    return tracks

# シーン合成時: ナレーション + SE を CompositeAudioClip でミックス
se_tracks = _build_se_tracks(scene.se_cues, SEPresetResolver())
if se_tracks:
    mixed = CompositeAudioClip([narration] + se_tracks)
    clip = clip.with_audio(mixed)
```

### BGM ミックス（最終出力レベル）

```python
# Phase 3: ffmpeg amix で BGM を重ねる（SE はすでにシーン MP4 に焼き込まれている）
self._mix_bgm(video, concat_path, output_path, scene_durations=scene_durations)
```

## この設計の利点

**BGM の調整が SE に影響しない。**

BGM の `volumeScale` を変えても、すでにシーン MP4 に焼き込まれた SE は影響を受けない。
SE の offset・音量は SE ファイル自体で制御できる。

**SE の追加が BGM ミックスロジックに干渉しない。**

SE を増やしても BGM ミックスのコードは変わらない。
SE は `CompositeAudioClip` の引数リストに追加するだけで、
ffmpeg amix フローは "音声付き動画に BGM を重ねる" というシンプルな責務を保てる。

**複数 SE の同時鳴らしが自然に扱える。**

```python
# 同じシーンに複数の SE を配置できる
CompositeAudioClip([
    narration,
    se1.with_start(0.0),   # シーン先頭
    se2.with_start(2.0),   # 2秒後
])
```

## 設計の原則

**「一緒に調整するもの」を同じフローに入れ、「独立して調整するもの」を分離する。**

SE と BGM は用途が違い、調整のタイミングも独立している。
同じフローに押し込むと「一方を変えたら他方が壊れた」という干渉が生まれる。

音声の多層ミックスでは、レイヤーの責務を先に決めることが実装の見通しを良くする：

- **Layer 1（シーン内）**: ナレーション + SE → クリップに焼き込む
- **Layer 2（最終出力）**: シーン動画 + BGM → 最終 MP4 を作る

## 教訓

- 音声処理を設計するとき、「どのレイヤーでミックスするか」を最初に決める
- SE のように「シーン局所的なもの」はシーンクリップに焼き込む
- BGM のように「動画全体に関わるもの」は最終出力フェーズで処理する
- 後から「SE と BGM を分けたい」とリファクタリングすると影響範囲が大きくなる
