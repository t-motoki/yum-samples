# 動画生成時にチャプタータイムスタンプを記録する設計

## 問題

YouTube 説明文のチャプタータイムスタンプを「後から」計算しようとすると、必ずずれる。

実際に起きた問題（ep3.5.5）：
- 動画の実尺: **2:46**
- WAV ファイルの合計から計算したタイムスタンプ: 最終章が **3:28**

ずれの原因は2つあった：

**原因1: WAV ファイルに重複が混入する**

```
audio/
  outro_まとめ_00_43c0327f.wav   ← 旧バージョンの台本で生成したファイル
  outro_まとめ_00_e2f4a2ad.wav   ← 現在の台本で生成したファイル（こちらが正）
```

台本を修正して再生成すると古い WAV が残り、glob がすべてを拾って重複計算した。

**原因2: WAV の尺が最終動画の尺と一致しない**

pause シーン（`<!-- pause: 3.0 -->`）や PiP クリップ（`<!-- clip: demo.mp4 pip=true -->`）は
WAV ファイルが存在しないため、計算から漏れる。
リップシンク処理が音声タイミングを変更するケースでも誤差が出る。

## 解決策: 動画生成時にタイムスタンプを記録する

タイムスタンプの計算を「後から推算する」のではなく、
動画を生成した直後に計算結果を `chapters.json` として保存する。

```
動画生成パイプライン
    │
    ├─ Phase 1: シーンを並列エンコード
    ├─ Phase 2: チャンク結合（xfade）
    └─ Phase 3: BGM ミックス
         │
         ▼
    _resolve_clip_durations()  ← クリップシーンの実尺を確定
         │
         ▼
    _calc_chapter_timestamps() ← セクションごとの開始時刻を計算
         │
         ▼
    chapters.json を出力        ← description.py が読む
```

### タイムスタンプ計算の核心

```python
def _calc_chapter_timestamps(scenes, scene_durations, video):
    """各 section_heading の動画内開始時刻を計算する。

    scene_durations: _resolve_clip_durations() が返すリスト
                     （clip_scene は VideoFileClip の実尺、それ以外は scene.duration_sec）
    """
    tr_sec_after = _calc_tr_sec_after(scenes, video)  # フェードオーバーラップ秒数
    chapters = {}
    current_sec = 0.0

    for idx, (scene, dur) in enumerate(zip(scenes, scene_durations)):
        heading = scene.section_heading
        if heading and heading not in chapters:
            chapters[heading] = round(current_sec, 3)
        # フェードオーバーラップ分を差し引いてタイムラインを進める
        current_sec += dur - tr_sec_after[idx]

    return chapters
```

フェードトランジション（`<!-- transition: fade -->`）はシーン同士が重なるため、
その分を差し引かないとタイムスタンプが後ろにずれていく。

### 出力形式（chapters.json）

```json
{
  "video_id": "ep3.5.5",
  "total_duration_sec": 166.5,
  "chapters": {
    "intro: 台本1行で効果音が鳴る": 0.0,
    "scene1: 課題提示": 13.2,
    "scene2: 解決方針": 32.1,
    "scene7: デモ": 144.3
  }
}
```

### 説明文生成側での読み込み

```python
def load_chapters(output_dir: Path) -> dict | None:
    chapters_path = output_dir / "chapters.json"
    if not chapters_path.exists():
        return None
    try:
        return json.loads(chapters_path.read_text(encoding="utf-8"))
    except Exception:
        return None  # 解析失敗は WAV-based 計算にフォールバック
```

`chapters.json` がなければ従来の WAV-based 計算にフォールバックするため、
古い動画の説明文を再生成する場合も壊れない。

## この設計の利点

**タイムスタンプが動画の実尺と一致する。**

`_resolve_clip_durations()` はクリップシーンの MP4 を実際に開いて尺を取得するため、
pause / PiP クリップ / リップシンク処理後の音声長が正確に反映される。

**WAV ファイルの重複問題に影響されない。**

タイムスタンプの計算は WAV ファイルを一切参照しない。
音声ファイルがどれだけ増えても、計算結果は変わらない。

**description.txt の再生成が正確になる。**

`python scripts/generate_description.py` を再実行しても、
`chapters.json` が存在すれば同じ正確なタイムスタンプが使われる。

## 設計の原則

**「後から推算できるもの」と「生成時しか計算できないもの」を区別する。**

タイムスタンプは動画生成プロセスの内部状態（フェード量・クリップ実尺・pause 秒数）に依存する。
これらは生成時にしか正確に把握できない。生成後に外部から再計算しようとすると必ずずれる。

「実行時に正確なデータが手に入る場所」で記録し、
後続のツールはその記録を読むだけにする。

## 教訓

- 「外部ファイルから後から計算できる」と思っていた値が、実は生成中間状態に依存していた
- 音声ファイルの glob は「現在の台本に対応するファイル」だけを拾う保証がない（残留ファイル問題）
- 中間成果物（音声ファイル）ではなく、生成プロセス自体がメタデータを出力する設計にする
- フォールバックを用意しておくと、既存の動画への影響なく新設計を導入できる
