# ffmpeg xfade で音声がずれる問題と解決策

## 問題

チャンク並列レンダリング後に ffmpeg `xfade` フィルターでチャンクをつなぐとき、音声が後半シーンで大幅にずれる（シーン3以降が消えたり、順序が乱れたりする）。

## 原因

`filter_complex` の音声フィルターを「チェーン concat」方式で書いたときに起きるバグ。

### 誤った設計（チェーン concat + 累積ストリームに atrim）

```
# k=0: チャンク0をトリム → チャンク1と結合 → [a01]（累積ストリーム）
[0:a]atrim=0:9.5,asetpts=PTS-STARTPTS[a0trim]
[a0trim][1:a]concat=n=2:v=0:a=1[a01]

# k=1: [a01]（チャンク0+1の累積、20秒）に atrim=0:9.5 → 9.5秒に切り詰め！
[a01]atrim=0:9.5,asetpts=PTS-STARTPTS[a1trim]
[a1trim][2:a]concat=n=2:v=0:a=1[a12]
```

`actual_durations[k]` はチャンク k 単体の秒数（例: 10.0s）なのに、`a_in` が前ステップの concat 出力（累積ストリーム）を指している。`atrim=0:9.5` を 20 秒の累積ストリームに適用すると、後半 10.5 秒が切り捨てられる。チャンクが増えるほど被害が拡大する。

## 対策：各チャンクを個別に atrim し、1 回の多入力 concat でまとめる

```
# 各チャンクの音声を独立してトリム（[k:a] を直接参照）
[0:a]atrim=0:9.5,asetpts=PTS-STARTPTS[a0trim]
[1:a]atrim=0:9.5,asetpts=PTS-STARTPTS[a1trim]
[2:a]atrim=0:9.5,asetpts=PTS-STARTPTS[a2trim]

# 1 回の concat=n=4 で全チャンクをまとめる
[a0trim][a1trim][a2trim][3:a]concat=n=4:v=0:a=1[aout]
```

ffmpeg の `concat` フィルターは `n=` で任意数の入力を受け取れる。これを使えば「累積ストリームへの誤 atrim」が構造上起きない。

## なぜ atrim が必要か

各チャンク（非最終）の末尾には無音バッファ（fade tr_sec 分）が付いている。映像は `xfade` のオーバーラップで消費されるが、音声は消費されずに残る。そのままつなぐと音声が映像より `N × tr_sec` 秒長くなり、映像が先に終わってずれる。

`atrim=0:(actual_duration - tr_sec)` で無音バッファだけを削除し、音声を映像長に揃える。

## 教訓

`filter_complex` のフィルターチェーンを書くとき、各ステップで「このラベルはどのストリームを指しているか」を確認する。特に:

- concat の出力ラベルを次ステップの入力に使うと、**累積ストリームへの操作**になる
- atrim・atempo など「ストリーム長を変える」フィルターは、**対象ストリームが想定通りの長さか**を意識する
- 多入力 concat（`concat=n=N`）は「チェーン concat + 累積への操作」を避けるシンプルな代替になる

## 関連

- [crossfade で音声がずれる問題と解決策](./crossfade-audio-timing.md)（チャンク内部の crossfade 音声ズレとその修正）
