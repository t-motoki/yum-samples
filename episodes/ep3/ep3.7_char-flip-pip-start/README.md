# ep3.7 char_flip per-scene / pip start=N

動画「完成しない —— ep3.x 振り返りと、次へ」のサンプルコードです。

振り返り回のために実装した2つのディレクティブを紹介します。

---

## 1. `char_flip` ディレクティブ（シーン単位の向き制御）

dialogue レイアウトで、キャラクターがどちらを向くかをシーン単位で切り替えられます。

```markdown
<!-- config: layout=dialogue -->
<!-- config: dialogue_order=yumu,sabacyan -->
<!-- config: dialogue_avatar_area=left -->

## S01: 通常会話（向き合い）

<!-- speaker: yumu -->
ここはふたりが向き合っています。

---

## S02: PiP 鑑賞シーン（ふたりが右を向く）

<!-- char_flip: true,true -->
<!-- pip: videos/ep3.0/video.mp4 position=right size=42% loop=false -->
<!-- speaker: yumu -->
ふたりとも右の PiP 動画を向いています。

---

## S03: 会話に戻る（向き合いに戻す）

<!-- char_flip: true,false -->
<!-- pip: stop -->
<!-- speaker: sabacyan -->
PiP が終わり、向き合いに戻りました。
```

### 値の意味

`<!-- char_flip: A,B -->` の A / B は `dialogue_order` の順番に対応します。

| 値 | 意味 |
| --- | --- |
| `true` | キャラクターを左右反転する（右向きになる） |
| `false` | 反転しない（左向きのまま） |
| `reset` | シーン単位の設定を解除してデフォルトに戻す |

### dialogue_avatar_area=left でのデフォルト動作

```
ゆむ（左）: デフォルト反転あり → 右向き（さばきゃんと向き合う）
さばきゃん（右）: デフォルト反転なし → 左向き（ゆむと向き合う）
```

PiP が右側にあるとき、両方を右向きにするには `<!-- char_flip: true,true -->` を使います。

---

## 2. `pip start=N` パラメータ（再生開始位置の指定）

pip ディレクティブに `start=N` を追加すると、指定した秒数から動画を再生できます。

```markdown
## S05: ep3.0 の核心シーン

<!-- pip: output/episodes/ep3.0/video.mp4 position=right size=42% loop=false start=100 pip_audio=false -->
最初に作ったのは、VOICEVOXで音声を出すだけのものでした。
```

冒頭から再生すると「どのエピソードも似たような始まり方」になりがちですが、
`start=N` で見せたいシーンから直接始められます。

### loop との組み合わせ

| loop | start の動作 |
| --- | --- |
| `loop=true` | `-ss N -stream_loop -1 -i path`（ffmpeg の seek で開始位置を指定） |
| `loop=false` | `trim=start=N,setpts=PTS-STARTPTS`（filter_complex でトリミング） |

---

## 使い方

```bash
# デモを実行する（パースと仕組みの説明）
python char_flip_pip_start_demo.py

# char_flip のパース結果だけ確認する
python char_flip_pip_start_demo.py char_flip

# pip start=N の ffmpeg コマンドを確認する
python char_flip_pip_start_demo.py pip_start
```
