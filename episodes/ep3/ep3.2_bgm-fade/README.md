# ep3.2 BGM フェードイン・フェードアウト — 台本から音量曲線を制御する

動画「BGMフェードイン・フェードアウト — 台本から音量曲線を制御する」のサンプルコードです。

## この動画でやること

```text
BGM が突然始まって突然終わる（before）
  → 冒頭でフワッと入り、末尾でフワッと消える（after）
```

台本の先頭に1行書くだけで制御できます。

```markdown
<!-- bgm-fade: 2.0 -->
```

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `bgm_fade_demo.py` | BGM フェードイン・フェードアウトのコアロジック デモ（moviepy のみで動く） |

---

## セットアップ

```bash
pip install moviepy
```

## 使い方

```bash
# BGM ファイルなしで動作確認（無音ファイルで代替）
python bgm_fade_demo.py

# 自前の BGM を使う場合
python bgm_fade_demo.py --bgm your_bgm.mp3 --fade 2.0 --duration 15
```

`output/bgm_faded.wav` に生成されます。

---

## 実装のポイント

### 3ステップで完結する

```python
# ① BGM を動画尺にループ
bgm_looped = afx.AudioLoop(duration=total_duration).apply(bgm_raw)

# ② 音量を下げる（ナレーションに被らないよう）
bgm_quiet = afx.MultiplyVolume(0.3).apply(bgm_looped)

# ③ 両端にフェードを適用
bgm_quiet = afx.AudioFadeIn(fade_sec).apply(bgm_quiet)
bgm_quiet = afx.AudioFadeOut(fade_sec).apply(bgm_quiet)
```

`afx.AudioFadeIn` / `afx.AudioFadeOut` は moviepy の組み込みエフェクト。
自前でフレームごとの音量計算を書く必要はありません。

### フェード秒数のチューニング

| 動画の尺 | 推奨フェード秒数 |
| --- | --- |
| 〜3分 | 1.0〜1.5秒 |
| 3〜8分 | 1.5〜2.5秒 |
| 8分〜 | 2.0〜3.0秒 |

短すぎると「ブツッ」と切れる印象、長すぎると冒頭で BGM が聞こえない時間が長くなります。

### シーン単位でフェードを使い分ける

BGM が途中で切り替わるシーン（例: 解説 → デモ）には、
各セクションの先頭にだけフェードインを適用できます。

```markdown
<!-- scene: INTRO, bgm: op_theme.mp3, bgm-fade-in: 1.0 -->
<!-- scene: DEMO,  bgm: ambient.mp3,  bgm-fade-in: 0.5 -->
```

`bgm-fade-in` はセクション単位、`bgm-fade` は動画全体の冒頭・末尾に対して機能します。
