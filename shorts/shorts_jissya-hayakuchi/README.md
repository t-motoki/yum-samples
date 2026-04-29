# shorts: 知らない人が口パクしてる

ショート動画「知らない人が口パクしてる」のサンプルです。

SadTalker で生成した実写風口パク動画を、アバターシーンの背面に PiP として重ねます。
最初は音声付きで最後まで再生し、その後は無音ループに切り替えるパターンを実演します。

## 主な技術

| 技術 | 説明 |
| --- | --- |
| SadTalker | 静止画＋音声から口パク動画を生成 |
| PiP `z_order=back` | PiP をアバターの背面（後ろ）に表示 |
| `pip_audio=true` | PiP 動画の音声を本編にミックス（初回再生用） |
| `pip_audio=false loop=true` | 無音ループに切り替え（解説シーン用） |
| Ken Burns | zoom+pan でPiP 登場を演出 |

## 台本パターン

```markdown
## S02: 実写さん登場（音あり・最後まで再生）

<!-- pip: path/to/sadtalker_output.mp4 pip_audio=true loop=false position=top-right size=80% z_order=back -->
<!-- ken_burns: zoom_start=1.0 zoom_end=1.5 pan_x=150 pan_y=-150 duration=5.0 -->
<!-- pause: 5.5 -->

---

## S03: ループ切り替え・解説

<!-- pip: path/to/sadtalker_output.mp4 pip_audio=false loop=true position=top-right size=80% z_order=back -->
<!-- speaker: yumu -->
口パクがちゃんと動きました。
```

### ポイント

- **同じ動画ファイルを2回 pip に書く**: 1回目は `pip_audio=true loop=false`（音あり・1回再生）、2回目は `pip_audio=false loop=true`（無音・ループ）。シーンを分けることで再生挙動を切り替える
- **`z_order=back`**: PiP をアバターより背面に置く。アバターが前面に立ったまま、背景で実写動画が流れる構図を作る
- **`size=80%`**: 縦型ショートでは大きめのサイズで迫力を出す

## SadTalker の使い方

SadTalker は静止画＋音声ファイルから口パク動画を生成するツールです。

```bash
# SadTalker のリポジトリは別途クローンが必要
# https://github.com/OpenTalker/SadTalker

cd /path/to/SadTalker

python inference.py \
  --driven_audio path/to/speech.wav \
  --source_image path/to/face_image.jpg \
  --result_dir output/ \
  --still \
  --preprocess full
```

### 主なオプション

| オプション | 説明 |
| --- | --- |
| `--still` | 頭の揺れを抑えて静止感を出す |
| `--preprocess full` | 顔全体を含む全身処理（デフォルトは顔のみ） |
| `--enhancer gfpgan` | GFPGAN で顔の解像度を上げる（オプション） |

出力された MP4 を `pip:` ディレクティブのパスに指定するだけで PiP として使えます。

## `bgm: stop` で間を演出する

```markdown
## S04b: 間

<!-- bgm: stop -->
<!-- pause: 1.2 -->
```

BGM を止めてポーズを置くことで「オチ前のため」を作ります。
SE（`<!-- se: バイオリン恐怖音1 -->`）と組み合わせると緊張感が増します。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `sadtalker_pip_demo.py` | PiP 切り替えパターンの台本パースデモ |

## 動かし方

```bash
python sadtalker_pip_demo.py
```

追加インストール不要（Python 標準ライブラリのみ）。
