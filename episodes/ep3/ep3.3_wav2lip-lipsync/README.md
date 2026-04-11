# ep3.3 Wav2Lip リップシンク — アニメキャラに口パクをつける

動画「Wav2Lip でリップシンク — アニメキャラに口パクをつける」のサンプルコードです。

## この動画でやること

```text
アニメキャラ画像 + 音声ファイル → Wav2Lip → 口パク動画
```

Wav2Lip はそのままではアニメ顔の検出が不安定です。
`--box` で口座標を手動指定すると安定して動きます。

```bash
python wav2lip_demo.py \
    --face   avatar.png \
    --audio  voice.wav  \
    --output out.mp4    \
    --box 345 465 380 620
```

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `wav2lip_demo.py` | Wav2Lip inference.py を Python から呼び出す最小ラッパー |

---

## セットアップ

```bash
# 1. Wav2Lip リポジトリを取得
git clone https://github.com/Rudrabha/Wav2Lip.git

# 2. 依存ライブラリをインストール
pip install torch torchvision librosa numpy opencv-python

# 3. モデルをダウンロードして Wav2Lip/checkpoints/ に置く
#    推奨: Wav2Lip-SD-NOGAN.pt（Wav2Lip GitHub の README 参照）
```

## 使い方

```bash
# 顔検出を自動で試みる（実写顔向け）
python wav2lip_demo.py --face avatar.png --audio voice.wav --output out.mp4

# アニメキャラ向け（--box で口座標を手動指定）
python wav2lip_demo.py --face avatar.png --audio voice.wav --output out.mp4 \
    --box 345 465 380 620
```

---

## 実装のポイント

### なぜアニメ顔では `--box` が必要か

Wav2Lip に組み込まれている顔検出器（S3FD）は実写顔で学習されています。
アニメ顔は輪郭・目・鼻の形が実写と大きく異なるため、口以外の領域を顔と誤認識することがあります。

`--box y1 y2 x1 x2` を使うと顔検出をスキップして、指定した領域に直接リップシンクを適用できます。

### `--box` の調整方法

```
画像座標系（左上が原点）

       x1=380  x2=620
  y1=345 +----------+
         |          |  ← 上半分: 鼻〜口元
         |    口    |
  y2=465 +----------+  ← 下半分: 口〜顎
```

- **box の下半分に口〜顎が収まるように指定する**
- 上半分が口元、下半分が顎になる座標を探す
- 少し広めに取るほうが自然な動きになる

### `--static True` で静止画モード

顔画像（動画ではなく PNG/JPG）を入力するときは `--static True` を指定します。
毎フレームの顔検出をスキップして初回のみ実行するため、処理が速くなります。

---

## 既知の制限

| 制限 | 詳細 |
| --- | --- |
| 品質 | LRS2（実写）で学習 → アニメ顔では口パクがやや不自然 |
| 速度 | CPU のみだと 1分の動画に 10〜30分かかる |
| 顔検出 | アニメ顔では `--box` 手動指定が事実上必須 |

Wav2Lip はアニメキャラへの適用が主目的ではないため、品質に限界があります。
より自然な動きが必要な場合は SadTalker など他のツールも検討してください。
