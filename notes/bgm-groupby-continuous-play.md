# BGM を複数シーンにわたって連続再生させる設計

## 問題

台本で複数の `##` シーンに `<!-- bgm: path -->` を書いたところ、シーンをまたぐたびに曲が最初から再生し直されてしまった。振り返り区間（S03〜S13）のような長いブロックで Stake Out を流し続けようとしても、シーンごとにリセットされる。

## 原因

BGM ミックスの実装（`_build_bgm_track`）は `groupby` で **連続する同一キーのシーンをまとめて1トラックにする** 仕組みになっている。

```python
for (bgm_path, bgm_volume, fade_in_sec), group in groupby(
    clip_durations, key=lambda x: (x[0], x[1], x[2])
):
    group_duration = sum(d for _, _, _, d in group)
    bgm_looped = AudioLoop(duration=group_duration).apply(AudioFileClip(bgm_path))
    # fade_in はグループ全体の先頭にのみ適用される
```

キーは `(bgm_path, bgm_volume, fade_in_sec)` の3要素。**1つでも異なると別グループになり、そのグループの先頭から曲が再生し直される。**

よくあるミス：

```markdown
## S03: 振り返り導入

<!-- bgm: src/assets/bgm/Stake Out.mp3 -->
<!-- bgm_volume: 0.25 -->
<!-- bgm_fade_in: 1.5 -->   ← fade_in あり: key = (Stake Out, 0.25, 1.5)
ナレーション

## S04: 続き

<!-- bgm: src/assets/bgm/Stake Out.mp3 -->
<!-- bgm_volume: 0.25 -->
                            ← fade_in なし: key = (Stake Out, 0.25, None)
ナレーション
```

S03 と S04 のキーが異なるため2グループになり、S04 で曲が再スタートする。

## 解決策

**連続再生させたいシーンは全て同一のキーを使う。**

`bgm_fade_in` を付ける場合は、そのブロック全シーンに同じ値を書く：

```markdown
## S03: 振り返り導入

<!-- bgm: src/assets/bgm/Stake Out.mp3 -->
<!-- bgm_volume: 0.25 -->
<!-- bgm_fade_in: 1.0 -->   ← 全シーン同じ key にする
ナレーション

## S04: 続き

<!-- bgm: src/assets/bgm/Stake Out.mp3 -->
<!-- bgm_volume: 0.25 -->
<!-- bgm_fade_in: 1.0 -->   ← 同じ
ナレーション

## S05: 続き

<!-- bgm: src/assets/bgm/Stake Out.mp3 -->
<!-- bgm_volume: 0.25 -->
<!-- bgm_fade_in: 1.0 -->   ← 同じ
ナレーション
```

この場合 S03〜S05 が1グループになり、`AudioLoop` でグループ全体の尺分ループされる。フェードインはグループ先頭（S03 の冒頭）にのみ適用される。

## 結果

- S03〜S13 が1トラック（約2分）として生成され、Stake Out が途切れずに流れる
- フェードインは S03 の冒頭 1.0 秒のみ適用される
- BGM が変わる S15（With You）から別グループが始まる

## BGM 設計のポイント

| 目的 | 書き方 |
|------|--------|
| 複数シーンで同じ曲を連続再生 | 全シーンに同一の `(bgm_path, bgm_volume, bgm_fade_in)` を書く |
| 曲切り替え時にフェードアウト | 切り替え直前のシーンで `bgm_volume: 0` にする（または BGM を省略して無音にする） |
| 新しい曲をフェードインで開始 | 新しい曲の最初のシーンだけに `bgm_fade_in: N` を書き、後続シーンも同じ値を維持する |
| グローバル BGM（全体デフォルト） | `<!-- config: bgm=path -->` で設定。section レベルの `<!-- bgm: -->` がないシーンに適用される |

## 教訓

`bgm_fade_in` は「このシーンの先頭でフェードイン」ではなく「このキーグループの先頭でフェードイン」として動く。シーン単位で個別に制御したい場合はキーを変えるしかないが、それは曲の再スタートを意味する。フェードインと連続再生は基本的にトレードオフ。
