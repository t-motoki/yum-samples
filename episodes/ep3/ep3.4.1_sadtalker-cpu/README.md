# ep3.4.1 SadTalker — CPU で静止画を動かす

動画「AIで静止画を動かす実験、13分待って気づいたこと」のサンプルコードです。

## この動画でやること

```text
顔画像（PNG）+ 音声（WAV）→ SadTalker → 顔が動くアニメーション動画（MP4）
```

GPU なし・CPU のみで動作します。
ただし処理は遅く、**3〜4 秒の動画に 10〜15 分**かかります。

```bash
python sadtalker_demo.py --image face.png --audio voice.wav
```

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `sadtalker_demo.py` | SadTalker inference.py を Python から呼び出す最小ラッパー |

---

## セットアップ

```bash
# 1. SadTalker リポジトリを取得
git clone https://github.com/OpenTalker/SadTalker.git

# 2. 依存ライブラリをインストール
cd SadTalker
pip install -r requirements.txt

# 3. モデルをダウンロード（SadTalker の README 参照）
#    checkpoints/ と gfpgan/weights/ に配置する
```

### インストールで詰まったら

SadTalker の依存ライブラリは壊れやすいです。以下が特にトラブルになりやすい：

```bash
# basicsr が古い numpy / torch に依存していてエラーになる場合
pip install basicsr --no-deps
pip install facexlib

# dlib のビルドエラーが出る場合（Linux）
sudo apt-get install cmake libboost-all-dev
pip install dlib
```

---

## 使い方

```bash
# 基本（still モード推奨: 頭の揺れを抑える）
python sadtalker_demo.py --image face.png --audio voice.wav

# 出力先を指定
python sadtalker_demo.py --image face.png --audio voice.wav --output my_results

# 頭の動きを有効にする
python sadtalker_demo.py --image face.png --audio voice.wav --no-still

# 高解像度（遅くなる）
python sadtalker_demo.py --image face.png --audio voice.wav --size 512
```

---

## 実装のポイント

### `--cpu` フラグ

SadTalker はデフォルトで CUDA GPU を使おうとします。
`--cpu` を渡すことで GPU なしで動作します。

### `--still` で頭の揺れを抑える

`--still` を指定しないと頭が大きく揺れ、実写風でない画像では不自然になりやすい。
アニメキャラや正面向きの静止画には `--still` が推奨です。

### 出力の場所

SadTalker は `result_dir` の中にタイムスタンプ付きのサブフォルダを自動生成します。

```
results/
  2026_03_16_22.48.39/
    face.mp4        ← 生成された動画
```

### 短い音声から試す

CPU 処理は非常に遅いため、最初は 3〜5 秒の音声で動作確認することを強く推奨します。
長い音声でいきなり試すと 1 時間以上待つことになります。

---

## 既知の制限

| 制限 | 詳細 |
| --- | --- |
| 速度 | CPU のみだと 3〜4 秒の動画に 10〜15 分かかる |
| 解像度 | デフォルト 256px（`--size 512` で改善できるが更に遅くなる） |
| 顔向き | 正面顔で最もきれいに動く。横顔・俯角は品質が落ちる |
| アニメ顔 | 実写顔で学習しているため、アニメキャラは顔検出が不安定なことがある |

---

## Wav2Lip との比較

| 項目 | Wav2Lip | SadTalker |
| --- | --- | --- |
| 動き | 口だけ | 顔全体（口・目・頭） |
| CPU 速度 | 遅い | さらに遅い |
| アニメ顔 | `--box` 手動指定で対応可 | 実写向けのため難あり |
| セットアップ | やや難 | 難 |
