# ep3.4.2 Rhubarb Lip Sync — CPU・無料でアニメキャラの口を動かす

動画「CPU・無料でアニメキャラの口を動かす — Rhubarb Lip Sync 調査記録」のサンプルコードです。

## この動画でやること

```text
音声（WAV）→ Rhubarb Lip Sync → 口の形タイミング JSON
                                   → アバター表情名（normal / lipsync_open / lipsync_half）
```

Rhubarb は映像を作らない。「この時刻にこの口の形」というデータを出力するだけです。
映像への適用は自分の Pillow レンダラー側で行います。

```bash
python rhubarb_demo.py --audio voice.wav
```

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `rhubarb_demo.py` | Rhubarb を呼び出して viseme タイミングを取得しアバター表情に変換するデモ |

---

## セットアップ

### 1. Rhubarb Lip Sync バイナリをダウンロード

[GitHub Releases](https://github.com/DanielSWolf/rhubarb-lip-sync/releases) から
OS に合ったバイナリをダウンロードして展開します。

```bash
# Linux の場合（v1.14.0）
wget https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip
unzip Rhubarb-Lip-Sync-1.14.0-Linux.zip
# 展開後: Rhubarb-Lip-Sync-1.14.0-Linux/rhubarb
```

Python ライブラリの追加インストールは不要です。標準ライブラリのみで動作します。

---

## 使い方

### 全 viseme タイムラインを表示

```bash
python rhubarb_demo.py --audio voice.wav
```

出力例:
```
[audio]   voice.wav
[rhubarb] rhubarb

総時間: 3.280s  / 12 cues

   start       end  viseme  expression
--------------------------------------------
   0.000     0.200       X  normal
   0.200     0.380       B  normal
   0.380     0.560       A  lipsync_open
   0.560     0.740       E  lipsync_half
   ...
```

### Rhubarb バイナリのパスを指定する

```bash
python rhubarb_demo.py --audio voice.wav --rhubarb /path/to/rhubarb
```

### 特定時刻の表情を問い合わせる

```bash
python rhubarb_demo.py --audio voice.wav --time 1.5
# → 時刻 1.500s → 表情: lipsync_open
```

---

## 実装のポイント

### Rhubarb は「データだけ」出力する

他の lip sync ツール（Wav2Lip・SadTalker）は映像を直接出力しますが、
Rhubarb は viseme タイミング JSON を出力するだけです。

```json
{
  "mouthCues": [
    { "start": 0.00, "end": 0.20, "value": "X" },
    { "start": 0.20, "end": 0.38, "value": "B" },
    { "start": 0.38, "end": 0.56, "value": "A" },
    ...
  ]
}
```

映像合成は既存のパイプラインで行えるため、既存の Pillow レンダラーにそのまま組み込めます。

### viseme → アバター表情のマッピング

Rhubarb の viseme は A〜H + X の9種類ですが、さばきゃんの表情絵は3種類に集約しています。

| Rhubarb viseme | 口の形 | さばきゃん表情 |
| --- | --- | --- |
| X（無音・休止） | 閉じる | `normal` |
| A（あ行系・大開口） | 大きく開く | `lipsync_open` |
| B（ん・閉音） | 閉じる | `normal` |
| C / D / E / F / G / H | 中間・半開き | `lipsync_half` |

### 指定時刻の表情を取得する

```python
from rhubarb_demo import extract_visemes, find_expression_at
from pathlib import Path

cues = extract_visemes(Path("voice.wav"))

# フレームレート 30fps なら、フレーム番号 → 秒数に変換して問い合わせる
for frame in range(90):  # 3秒分
    time_sec = frame / 30.0
    expression = find_expression_at(cues, time_sec)
    print(f"frame {frame:3d} ({time_sec:.3f}s) → {expression}")
```

---

## SadTalker・Wav2Lip との比較

| 項目 | Wav2Lip | SadTalker | Rhubarb Lip Sync |
| --- | --- | --- | --- |
| 出力 | 映像（MP4） | 映像（MP4） | viseme タイミング JSON |
| CPU 速度 | 遅い | 非常に遅い | **速い（数秒）** |
| アニメ顔 | `--box` 手動指定で対応可 | 実写向けのため難あり | **アニメ向け実績多数** |
| GPU | 必要 | 必要 | **不要** |
| 口の動き | ピクセル変形（滑らか） | 顔全体アニメ | 絵の切り替え（パラパラ感あり） |
| セットアップ | やや難 | 難 | **バイナリ1つ** |

### Rhubarb の制限

- 口の形を細かく「変形」させるのではなく、表情絵を「切り替える」仕組みのため動きが単調になりやすい
- 表情の種類を増やすほど口パク感は上がるが、準備コストも増える
- 音素の種類が英語ベースのため、日本語音声では一部 viseme の割り当てが粗くなることがある
