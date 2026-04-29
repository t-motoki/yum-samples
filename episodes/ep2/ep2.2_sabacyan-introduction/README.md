# ep2.2 さばきゃん登場 — 聞いてくれる人がいるだけで、こんなに違う

動画「ひとりで話し続けて気づいたこと — 聞いてくれる人がいるだけで、こんなに違う」のサンプルコードです。

ep2.2 はキャラクター紹介回のため技術デモの比重は低めですが、
このエピソードに向けて3つの実装をしています。

## この動画でやったこと

### 1. 2キャラクターサムネイルレイアウト

```text
キャラクターが1人（before）
  → 2人を左右に並べて「対話感」を出す（after）
```

主役（さばきゃん）を右・大きく、サブ（ゆむ）を左・小さく配置することで
サムネイルに奥行きが生まれます。

### 2. `thumbnail-subtext` ディレクティブ

台本の先頭コメントからサムネイルのサブテキストを制御できるようにしました。

```markdown
<!-- thumbnail-subtext: さばきゃん、はじめまして -->
```

省略すると「無料ツールだけで完結」がデフォルトで入ります。
空文字列 `<!-- thumbnail-subtext:  -->` でサブテキストなしにできます。

### 3. VOICEVOX 音量の底上げ（volumeScale）

他チャンネルと比較して音量が低かった問題を修正。
YouTube の目安（-14 LUFS）に合わせて `volumeScale=2.0` をデフォルトにしました。

```python
# 環境変数で上書き可能
VOICEVOX_VOLUME=1.5 python generate_episode.py script.md
```

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `thumbnail_two_chars_demo.py` | 2キャラクターサムネイル生成デモ（Pillow のみで動く） |

---

## セットアップ

```bash
pip install pillow
```

## 使い方

```bash
# キャラクター画像なしでも動作確認できる（ダミー矩形で代替）
python thumbnail_two_chars_demo.py

# 自分のキャラクター画像を使う場合
python thumbnail_two_chars_demo.py --char1 yumu.png --char2 sabacyan.png
```

`output/thumbnail_demo.jpg` に生成されます。

---

## 実装のポイント

### 2キャラクターのレイアウト設計

```python
LAYOUT = {
    "char1": {"target_h": 400, "x": 230, "y_offset": 10, "mirror": True},   # 左・小さめ（サブ）
    "char2": {"target_h": 620, "x": 900, "y_offset": 10, "mirror": False},  # 右・大きめ（主役）
}
```

| パラメータ | 意味 |
| --- | --- |
| `target_h` | 画像の高さ（縦基準でリサイズ）。これで「大きさ」を制御 |
| `x` | キャラクター中心の X 座標 |
| `y_offset` | 下端からのオフセット。正の値で上にずらす |
| `mirror` | 左右反転。内側を向かせるために左キャラを反転 |

### 配置の計算

```python
y = H - target_h + y_offset  # 下揃え基準で配置
```

下端揃えにすることで、サイズが違っても「地に足がついている」自然な配置になります。

### キャラクターの重なり順

左キャラを先に描いてから右キャラを描くと、右キャラが前面に来ます。

```python
place_character(canvas, img1, spec1)  # サブ（奥）
place_character(canvas, img2, spec2)  # 主役（手前）← 後から描くので上に重なる
```

### thumbnail-subtext ディレクティブの仕組み

台本 Markdown のコメント行を正規表現なしで解析しています。

```python
elif line.startswith("<!-- thumbnail-subtext:"):
    thumbnail_subtext = line.removeprefix("<!-- thumbnail-subtext:").rstrip().removesuffix("-->").strip()
```

`str.removeprefix()` / `str.removesuffix()` は Python 3.9 以上で使えます。
