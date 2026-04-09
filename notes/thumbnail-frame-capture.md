# 動画フレームをサムネイル背景に使う（ep5.0）

## 問題

既存のサムネイル生成（`generate_thumbnail.py`）はマトリックスレイン背景＋キャラ画像の固定スタイルだった。他チャンネルのように「動画の切り抜きを背景に使う」スタイルに対応していなかった。

---

## 解決策

`--frame-video` と `--frame-time` オプションを追加した。

```bash
python scripts/generate_thumbnail.py \
  --frame-video output/episodes/ep5.0/video.mp4 \
  --frame-time 120.5 \
  --title "Claude Codeが迷わなかった3つの仕掛け" \
  --subtext "整えたから動いた。指示はしていない" \
  --output output/episodes/ep5.0/thumbnail.jpg
```

### フレームモードの処理

```python
# ffmpeg でフレームを抽出
ffmpeg -loglevel error -ss 120.5 -i video.mp4 -vframes 1 -f image2pipe -vcodec png pipe:1

# 下半分にグラデーションオーバーレイ（alpha 0 → 180）
draw_lower_gradient_overlay(canvas)

# タイトルとラベルを重ねる（キャラ画像なし）
```

---

## 通常モードとの違い

| | 通常モード | フレームモード |
|---|---|---|
| 背景 | マトリックスレイン（コード文字） | 動画の1フレーム |
| キャラ画像 | あり（ゆむ・さばきゃん） | なし |
| ラベル | あり | あり |
| タイトル位置 | 下部 | 下部（グラデーション上） |
| 用途 | ep1〜ep4 の汎用 | 動画の内容が一目でわかるシーン向け |

---

## サムネイルに使うフレームの選び方

- 動画生成後に `tmux attach -t yum-generate` で完了を確認
- `ffmpeg -i video.mp4 -vf fps=0.1 frames/%04d.png` で10秒ごとにフレームを書き出して選ぶ
- または動画プレイヤーでいいシーンの秒数を記録して `--frame-time` に渡す

---

## 関連

- `scripts/generate_thumbnail.py` — `extract_frame()` / `draw_lower_gradient_overlay()` を追加
- `tests/scripts/test_generate_thumbnail_frame.py` — テスト
- `docs/design/thumbnail_frame_mode.md` — 設計ドキュメント
