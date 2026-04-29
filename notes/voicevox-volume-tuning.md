# VOICEVOX 音量チューニング — YouTube の音量基準に合わせる

VOICEVOX のデフォルト音量は YouTube の推奨ラウドネス（-14 LUFS）に対して低すぎる問題と、
その対処方法を記録します。

## 問題

他チャンネルの動画と並べて再生すると、ナレーション音量が明らかに小さかった。
視聴者が音量を上げてから見る必要があり、体験として良くない。

## 原因

YouTube は動画をアップロード時に **-14 LUFS** に正規化する（ラウドネス正規化）。
VOICEVOX のデフォルト出力は -23〜-20 LUFS 程度と低めのため、
YouTube の正規化後も他チャンネル比で音量が小さく聞こえる。

## 対処: volumeScale パラメータの調整

VOICEVOX の音声合成クエリに `volumeScale` を設定することで、合成音声の音量を底上げできる。

```python
query["volumeScale"] = 2.0  # デフォルト 1.0 の2倍に底上げ
```

環境変数で外から制御できるようにしておくと調整が楽：

```python
import os
volume_scale = float(os.getenv("VOICEVOX_VOLUME", "2.0"))
query["volumeScale"] = volume_scale
```

```bash
# 通常はデフォルトで起動
python generate_episode.py script.md

# 音量を調整したいときだけ上書き
VOICEVOX_VOLUME=1.5 python generate_episode.py script.md
```

## volumeScale の目安

| volumeScale | 用途 |
| --- | --- |
| 1.0 | VOICEVOX デフォルト（小さい） |
| 1.5 | 若干の底上げ |
| **2.0** | YouTube -14 LUFS に近づく（推奨） |
| 3.0 以上 | クリッピング（音割れ）が起きる可能性 |

## BGM と重ねる場合の音量バランス

ナレーションを底上げしたうえで BGM を重ねる場合、BGM 側も調整が必要。

```python
# BGM は MultiplyVolume で 30% 程度に抑える
bgm_quiet = afx.MultiplyVolume(0.3).apply(bgm_looped)
```

ナレーションが主役なので BGM はあくまで環境音として扱う。
-20dB（= MultiplyVolume(0.1)）〜-10dB（= MultiplyVolume(0.3)）の範囲で調整する。

## 確認方法

ffmpeg の `loudnorm` フィルタで生成した動画のラウドネスを測定できる。

```bash
ffmpeg -i output.mp4 -filter:a loudnorm=print_format=json -f null -
```

`input_i` の値が -14 に近ければ OK。
