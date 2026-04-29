# PiP オーバーレイ設計ノート（ep3.6）

## 問題

「操作画面を見せながら話す」演出がなかった。

既存の `clip: pip=true` はスクリーン録画を全画面クリップとして再生し、その左下にアバターを小窓表示するモードだったが、**別ファイルとして事前に用意した MP4 を指定する必要があった**。アバターが話している最中に録画映像を画面隅に重ねながら会話を続ける、というスタイルには対応していなかった。

```markdown
<!-- 既存: clip: に全画面録画ファイルを指定する必要があった -->
<!-- clip: screen_recording.mp4 pip=true -->
（会話はここで止まり、録画が全画面で流れる）
```

台本を読む人（制作者）が自然に書けて、かつシーンをまたいで録画を流し続けられる仕組みが必要だった。

---

## 解決策

`<!-- pip: file.mp4 position=right size=45% -->` を台本に1行書くだけで PiP オーバーレイが有効になるディレクティブを追加した。

```markdown
<!-- pip: screen_recording.mp4 position=right size=45% -->

## シーン1

<!-- speaker: yumu -->
では、実際に動かしてみましょう。

## シーン2

<!-- speaker: sabacyan -->
あ、ここに表示が出てますね！

<!-- pip: stop -->
```

このディレクティブは `<!-- pip: stop -->` まで `##` をまたいで持ち越す（`current_speaker` と同じセマンティクス）。制作者は「いつから見せるか・いつ止めるか」だけを書けばよい。

パラメータ:

| パラメータ | デフォルト | 説明 |
| ---------- | ---------- | ---- |
| `position` | `bottom-right` | 配置位置（`top-left` / `top-right` / `bottom-left` / `bottom-right` / `center` / `left` / `right` 等） |
| `size` | `30%` | PiP ウィンドウ幅を出力動画幅に対する割合で指定 |
| `loop` | `true` | PiP 動画が本編より短い場合にループするか。`false` で最終フレーム静止 |
| `pip_audio` | `false` | `true` のとき PiP 動画の音声を本編音声と amix する |

---

## 仕組み

### フェーズ3b: BGM ミックス後の全体動画に合成する

動画生成のフェーズ構成は以下のとおり。PiP オーバーレイは Phase 3b として追加した:

```
Phase 1: シーン単位のチャンク並列エンコード（MoviePy）
Phase 2: チャンク結合（ffmpeg xfade concat / -c copy）
Phase 3a: BGM ミックス（ffmpeg amix）
Phase 3b: PiP オーバーレイ（ffmpeg overlay）  ← ここ
```

Phase 1 で適用すると、各チャンクが独立した PiP タイムコードを持ちシーン境界でリセットされてしまう。Phase 3b では動画全体を1本のファイルとして受け取るため、シーンをまたいだ連続再生が自然に実現できる。

### `_build_pip_segments()`: 連続シーンをセグメントに結合する

同一 `PipConfig` を持つ連続シーンを1つのセグメントにまとめ、タイムコードをシーン境界でリセットしないことを保証する。

```python
# PipConfig が変わるまで duration を累積してオフセットを計算する
segments = []
current_pos = 0.0
for scene, duration in zip(video.scenes, scene_durations):
    if scene.pip:
        segments.append((scene.pip, current_pos, current_pos + duration))
    current_pos += duration
```

結果として `[(PipConfig, start_sec, end_sec), ...]` のリストが得られ、`_ffmpeg_pip_overlay` に渡される。

### `-stream_loop -1 -t duration`: ループ再生の実装

PiP 動画が本編より短い場合に `loop=true`（デフォルト）でループ再生する。ffmpeg の入力オプション `-stream_loop -1` で入力を無限ループし、`overlay` フィルターの `enable='between(t,start,end)'` で区間を制限する。

```
ffmpeg -y \
  -i video_path \
  -stream_loop -1 -i pip_path \
  -filter_complex "[1:v]scale={pip_w}:-2[pip_scaled];
                   [0:v][pip_scaled]overlay=x={x}:y={y}:enable='between(t,start,end)'[vout]" \
  -map "[vout]" -map 0:a? ...
```

`-stream_loop -1` は **`-i pip_path` の前**に置く必要がある（後置すると無効になる落とし穴）。

### `tpad=stop=-1:stop_mode=clone`: 最終フレーム静止

`loop=false` のとき、PiP 動画の尺が切れた後に最終フレームを静止させる。`tpad=stop=-1:stop_mode=clone` でストリーム末尾フレームを無限複製し、最終フレームの静止を実現する。

```
[1:v]tpad=stop=-1:stop_mode=clone[pip_padded];
[pip_padded]scale={pip_w}:-2[pip_scaled];
[0:v][pip_scaled]overlay=x={x}:y={y}:enable='between(t,start,end)'[vout]
```

### `amix` フィルター: `pip_audio=true` での音声ミックス

`pip_audio=true` のとき、PiP 動画の音声を本編音声と `amix` でミックスする。`pip_audio=false`（デフォルト）では本編音声のみを出力し、既存動作を維持する。

音声ミックスの設計ポイント:
- `any_pip_audio` で「いずれか1つでも `pip_audio=True` なら True」と判定してブランチを2択に絞る
- `amix` 前に `ffprobe` で PiP ファイルの音声ストリームの有無を確認する（音声ストリームのない PiP を `[N:a]` に渡すと ffmpeg がエラーになる）
- `amix` を通った後の音声は PCM になるため `-c:a aac` で再エンコードする（`-c:a copy` は不可）
- `dropout_transition=0` を明示しないと入力が切れた瞬間に音量急降下フェードが発生する

---

## テロップとの共存

bottom 系プリセット（`bottom-left` / `bottom-right` / `center-bottom`）がテロップバーに重なる問題を `telop_bar_y` 引数で解決した。

```python
bottom_y_expr = (
    f"{telop_bar_y}-h-{_PIP_MARGIN}"
    if telop_bar_y is not None
    else f"H-h-{_PIP_MARGIN}"
)
```

`telop_bar_y=None` のデフォルトで後方互換を保ちつつ、呼び出し元（`compose()` / `_compose_sequential()`）が `get_metrics(video.layout).telop_bar_y` を渡すことですべてのポジションで「テロップバーに重ならない」ことが保証される。

ポジションクランプは `bottom_y_expr` の計算に集約されており、ポジションごとに条件分岐を書かなくてよい。

---

## `dialogue_avatar_area` との組み合わせ

PiP を右側に表示しながら2キャラクターを左側に寄せて「2人で鑑賞」の構図を作れる。

```markdown
<!-- config: dialogue_avatar_area=left -->
<!-- pip: screen_recording.mp4 position=right size=45% -->
```

`dialogue_avatar_area=left` のとき、dialogue レイアウトの2キャラクターの center_x が左半分（VIDEO_W=1920 なら 240 / 720）に配置される。

| `dialogue_avatar_area` | VIDEO_W=1920 | 左キャラ center_x | 右キャラ center_x |
|---|---|---|---|
| `"full"` | 1920 | 480 | 1440 |
| `"left"` | 1920 | 240 | 720 |
| `"right"` | 1920 | 1200 | 1680 |

既存の `is_pip_scene()`（`clip: pip=true` モード）とは独立しており、統合しない。`is_pip_scene()==True` のときは `PIP_CHAR_AREA_W` の既存ロジックが優先される。

---

## 設計判断

### なぜ Phase 3b（後処理）にしたか

Phase 1（シーン単位のチャンクエンコード）で PiP を適用すると、各チャンクが独立した PiP タイムコードを持つ。シーン境界で PiP タイムコードがリセットされ「連続再生」が実現できない。

Phase 3b では動画全体を1本のファイルとして受け取り、1回の ffmpeg コマンドで全区間のフィルターグラフを適用できる。BGM ミックスと同じ構造（動画全体に後付けで適用）にすることで実装の一貫性を保てる。

計算コストの観点でも、各シーンに個別に overlay を適用する（シーン数分の ffmpeg 起動）より、動画全体に対して1回だけ適用する方が効率的。

### warn + skip 設計: ファイルが見つからなくても生成を止めない

PiP ファイルが存在しない場合は `stderr` に警告を出してそのセグメントをスキップし、PiP なしで生成を継続する。

この設計を採用した理由:
- 動画生成は28分かかる。ファイルパスのタイプミス1つで全体が失敗するのは損失が大きい
- PiP は「あれば便利な補助画面」であり、なくても本編映像は成立する
- `clip:` 全画面モードは「クリップなしではシーンが成立しない」ため `FileNotFoundError` を raise するが、PiP とは性質が異なる
- BGM も同じ `warn + skip` 設計を採用している
- `--preview-only` モードのバリデーションフェーズでファイルの存在確認を事前に行える

---

## 教訓

- **「どこに置くか」で実装の複雑さが大きく変わる**: Phase 1 で実装しようとすると「シーンをまたぐタイムコード継続」のために複雑な状態管理が必要になる。「全体動画に後付け」という発想の転換で実装がシンプルになった
- **`-stream_loop -1` は `-i` の前に置く**: 後置すると無効になる。ffmpeg の入力オプションは対応する `-i` の直前に書く
- **`scale=-1` より `scale=-2`**: H.264 は幅・高さが2の倍数でなければエラーになる。`-1`（奇数になり得る）ではなく `-2`（2の倍数への丸め）を使う
- **`amix` 後は `-c:a copy` 不可**: フィルターを通った音声は PCM になるためコピーではなく再エンコードが必要。`pip_audio=false` のパスでは既存の `-c:a copy` を維持して既存テストを壊さないことが重要
- **テロップとの共存は「全ポジション統一クランプ」で解決する**: ポジションごとに条件分岐を書くより、`bottom_y_expr` に集約する方が追加ポジション（`center-bottom` 等）にも一貫して適用できる
- **既存概念との名前衝突に注意**: `clip: pip=true` の `is_pip_scene()` と新しい `pip:` ディレクティブの `is_pip_overlay_scene()` は別概念。命名を明確に分けることで混乱を防いだ

---

## ep3.6 フォローアップ: 実装後に発見したバグ群（2026-04-01）

実装後の本番生成で4つのバグが発覚した。テスト動画では再現しなかった理由も含めて記録する。

### バグ1: section END-state 問題（pip がシーンに反映されない）

**症状**: `intro` シーンで PiP が表示されない。`scene3f` でも PiP が表示されない。

**原因**: `markdown_reader.py` の第1パスで `section["pip"]` はセクション終了時点の `current_pip` を記録していた。`intro` セクション内で `<!-- pip: ... -->` と `<!-- pip: stop -->` が両方あると、セクション END 状態は `None`（stop 後）になる。第2パスで全シーンに `pip=None` が割り当てられた。

**修正**: `current_items` に pip ディレクティブを追加するパターン（`dialogue_avatar_area` と同じ設計）。第2パスで item を順に処理して `section_pip` を更新する。

**なぜテストで見抜けなかったか**: pip-v2 テストスクリプトは各セクションで pip:start か pip:stop のどちらか一方しか持っておらず、「同一セクションに start と stop が共存する」パターンが存在しなかった。

---

### バグ2: video_dialogue_avatar_area の汚染

**症状**: 最初のシーンからアバターが右側に寄っている（`scene3f` の `dialogue_avatar_area=left` が全シーンに適用されていた）。

**原因**: `markdown_reader.py` のセクション内で `dialogue_avatar_area` config が検出されると `video_dialogue_avatar_area`（Video レベルのデフォルト）を上書きしていた。

**修正**: `not current_id`（セクション外）の場合のみ `video_dialogue_avatar_area` を更新する。セクション内では `current_dialogue_avatar_area` のみを変更する。

**なぜテストで見抜けなかったか**: pip-v2 では `scene4` に `dialogue_avatar_area=left` を置いた後に `scene5` で `dialogue_avatar_area=full` にリセットしていた。Video デフォルトが汚染されてもシーン内の上書きで中和されていた。

---

### バグ3: local-t 問題（loop=false z_order=back pip が 0〜Ns をループ）

**症状**: `screen_edit.mp4`（73秒）が 0〜6秒をループし続ける。

**原因**: MoviePy の `_make_frame(t)` は各シーンに対して `t=0` から始まるローカル時刻を渡す。`_draw_pip_overlay_frame()` は `t` をそのまま pip 動画の再生位置として使うため、シーンをまたぐたびに 0 秒に戻ってしまう。

**修正**: 各シーンのチャンク内累積開始時刻 `pip_global_offset` を事前計算してクロージャ経由で `render()` に渡す。`_draw_pip_overlay_frame()` では `global_t = t + pip_global_offset` を pip 動画の再生位置として使う。

**設計の要点**: `pip_global_offset` は `tr_sec_after` も含めて累積する（フェードバッファ分も正しく加算するため）。

---

### バグ4: AAC 末尾音声切れ（pip_audio=true パス）

**症状**: `pip_audio=true` を使うと最後の音声が数十ミリ秒分切れる。`-c:a copy` パスでは発生しない。

**原因**: `amix` を通った後に AAC 再エンコードが走る。AAC は 1024 サンプル（44100Hz で約 23ms）単位でフレームを処理するため、最後の不完全フレームが失われる。

**修正**: `amix` → `[amixed]` → `apad=whole_dur={total_duration}` → `[aout]` の順でパディングを挿入してから `-t` で切る。

```
[a0][a_pip_gated0]amix=inputs=2:duration=first:dropout_transition=0[amixed];
[amixed]apad=whole_dur=199.6[aout]
```

**教訓**: `amix + -c:a aac` の組み合わせでは末尾パディングが必須。`-c:a copy` パスでは不要。
