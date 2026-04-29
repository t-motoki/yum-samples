# pip ディレクティブで静止画を表示する（ep5.0）

## 問題

コードや仕様書のスクリーンショットをアバターと並べて表示したかった。

既存の `pip:` ディレクティブは動画（`.mp4`）のみ対応。`clip: pip=true` は MoviePy 経由のため画像ファイルを読めない。

```markdown
<!-- これは動く（動画） -->
<!-- pip: screen_recording.mp4 position=right size=45% -->

<!-- これは動かなかった（画像） -->
<!-- clip: screenshot.png pip=true -->  ← MoviePy が PNG をビデオとして読めない
```

---

## 解決策

`_ffmpeg_pip_overlay()` に画像拡張子の分岐を追加した。

```python
_IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg"})

# 画像の場合: -loop 1 で静止フレームとして扱う
if config.path.suffix.lower() in _IMAGE_EXTS:
    input_args = ["-loop", "1", "-i", str(config.path)]
    # tpad 不要（ループで長さが確保される）
else:
    input_args = ["-stream_loop", "-1", "-i", str(config.path)]
```

`ffmpeg -loop 1 -i image.png` で PNG を「無限ループする静止フレーム動画」として扱い、
動画と同じ PiP オーバーレイのパイプラインに乗せる。

---

## 台本での使い方

```markdown
<!-- シーンをまたいで表示したいときは pip: ディレクティブを使う -->
<!-- pip: inputs/episodes/ep5.0/claude_md_screenshot.png position=right size=45% -->
<!-- speaker: yumu -->
CLAUDE.mdっていうファイルがあって、最初に読む場所を指してる。

---

<!-- 次のシーンでも同じ画像が表示され続ける -->
<!-- speaker: yumu -->
計算モデルを独断で決めるなとか、そういうことも書いてある。

<!-- pip: stop -->
```

---

## 動画 PiP との違い

| | 動画 PiP | 画像 PiP |
|---|---|---|
| ffmpeg オプション | `-stream_loop -1 -i video.mp4` | `-loop 1 -i image.png` |
| `tpad` フィルタ | 不要（ループ指定） | 不要 |
| 台本の書き方 | 同じ `pip:` ディレクティブ | 同じ `pip:` ディレクティブ |
| 用途 | 操作デモ・録画 | スクリーンショット・図解 |

---

## 関連

- `src/infrastructure/video/moviepy_composer.py` — `_ffmpeg_pip_overlay()` に実装
- `tests/infrastructure/video/test_moviepy_composer_pip_image.py` — テスト
- `docs/design/pip_image_support.md` — 設計ドキュメント
