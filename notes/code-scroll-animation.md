# コードスクロール演出 — 全体を見せてから一行に絞る

技術系動画でコードを見せるとき、「全体 → キーの一行」という二段構成が
視聴者の理解を助けます。このパイプラインでの実装パターンを記録します。

## 問題意識

コードの解説動画でありがちな失敗:

- いきなり差分（diff）を見せる → 「これがどこのコードか？」がわからない
- コード全体をずっと表示 → どこを見ればいいかわからない
- テキストで説明するだけ → 抽象的すぎてイメージできない

## 解決パターン: 全体スクロール → キーの一行ズームイン

```text
1. 「実装全体を先に見ておきましょう」（ナレーション）
2. コード全体を表示（18行超でスクロールが自動発動）
3. 5秒かけてコードが上から下へ流れる
4. 「ポイントはこの一行だけです」（ナレーション）
5. diff で該当行だけを大きく表示
```

視聴者は「全体像を把握してから詳細に集中できる」。

## 台本の書き方

```markdown
ゆむ「実装全体を先に見ておきましょう。」

```python
def _build_bgm_track(clip_durations, afx, AudioFileClip, ...):
    audio_segments = []
    current_pos = 0.0
    for (bgm_path, bgm_volume, fade_in_sec), group in groupby(...):
        group_duration = sum(d for _, _, _, d in group)
        if bgm_path and Path(bgm_path).exists():
            bgm_raw = AudioFileClip(str(bgm_path))
            bgm_looped = afx.AudioLoop(duration=group_duration).apply(bgm_raw)
            effective_volume = bgm_volume if bgm_volume is not None else default_bgm_volume
            bgm_quiet = afx.MultiplyVolume(effective_volume).apply(bgm_looped)
            if fade_in_sec is not None and fade_in_sec > 0.0:
                bgm_quiet = afx.AudioFadeIn(fade_in_sec).apply(bgm_quiet)
            audio_segments.append(bgm_quiet.with_start(current_pos))
        current_pos += group_duration
    ...
` ` `

<!-- pause: 5 -->

<!-- expression: surprise -->
ゆむ「ポイントはこの一行だけです。」

` ` `diff
+ if fade_in_sec is not None and fade_in_sec > 0.0:
+     bgm_quiet = afx.AudioFadeIn(fade_in_sec).apply(bgm_quiet)
` ` `
```

## スクロール発動の仕組み

コードブロックの行数が **18行を超える** と自動的にスクロール演出が発動する。

```python
MAX_LINES = 17  # これを超えるとスクロール開始

if len(code_lines) > MAX_LINES:
    # スクロールアニメーション（VideoClip）
    scroll_lines = len(code_lines) - MAX_LINES
    def make_frame(t):
        scroll_offset = int(t / duration * scroll_lines)
        visible = code_lines[scroll_offset : scroll_offset + MAX_LINES]
        return render_code_frame(visible)
    clip = VideoClip(make_frame, duration=duration)
else:
    # 静止表示（ImageClip）
    clip = ImageClip(render_code_frame(code_lines)).with_duration(duration)
```

## `pause` ディレクティブとの連携

`<!-- pause: N -->` を使うと N 秒間、ナレーションなしでコードが表示され続ける。
このとき、直前のコードブロックが `prev_code` として引き継がれ、
スクロール中も同じコードが表示される。

```text
コードブロック表示（スクロール開始）
    ↓ 5秒間スクロール（pause: 5）
コードスクロール完了
    ↓
diff 表示（キーの一行をハイライト）
```

## スクロール速度の目安

```text
スクロール行数 = コード行数 - 17
推奨 pause 秒数 = スクロール行数 / 6  （6行/秒が視認しやすい速度）
```

| コード行数 | スクロール行数 | 推奨 pause |
| --- | --- | --- |
| 20行 | 3行 | 2〜3秒 |
| 30行 | 13行 | 3〜4秒 |
| 50行 | 33行 | 5〜6秒 |
| 70行以上 | 53行以上 | 7秒以上 |

速すぎると視聴者がコードを追えない。遅すぎると中断したくなる。
「コード全部は読まなくていいが、何となく量感がわかる」速度が理想。
