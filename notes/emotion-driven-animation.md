# 感情連動アニメーション: 「既存の仕組みを流用する」設計の考え方

ep3.4.3 でアイドルアニメーション（sin 波による常時揺れ）を実装した後、
ep3.4.4 で「感情ラベルに応じて体の動きを変える」仕組みを追加したときの設計記録。

## 問題

アイドルアニメーションを実装したことで、キャラクターは常にゆらゆら揺れるようになった。
ただし感情が変わっても揺れ方が変わらない。joy でも surprise でも同じリズムが続く。

```
before: 感情が変わっても体は同じゆらゆら
after:  joy → 弾む、surprise → 横揺れ、thinking → ズームイン
```

## 設計の核心: `calc_emotion_offset()` で感情→オフセットを決める

すべての感情アクションを1つの関数に集約した。

```python
def calc_emotion_offset(emotion, t, scene_elapsed) -> tuple[int, int, float]:
    # 返り値: (offset_x, offset_y, scale)
```

感情ラベルと時刻を受け取って `(offset_x, offset_y, scale)` の3値を返すだけ。
描画ループはこの3値を受け取るだけでよく、感情の種類を知らなくてよい。

## 各アクションの実装

### joy → bounce（sin 波の流用）

```python
if emotion == "joy":
    joy_amplitude = idle_amplitude * 2.0  # 振幅2倍
    joy_frequency = idle_frequency * 2.0  # 周波数2倍
    offset_y = int(joy_amplitude * math.sin(2 * math.pi * joy_frequency * t))
```

ep3.4.3 で作った sin 波と**まったく同じ式**。振れ幅と周波数を変えるだけ。
新しい計算式はゼロで「弾んでいる」感じが出た。

### surprise → shake（ランダム左右）

```python
elif emotion == "surprise":
    offset_x = random.choice([-amp, amp])  # フレームごとにランダム
```

`random.choice` で `-amp` か `+amp` を毎フレーム選ぶ。
このランダムなちらつきが「驚いて体が震える」感じを演出する。

### thinking → zoom_in（線形拡大）

```python
elif emotion == "thinking":
    progress = min(scene_elapsed / zoom_duration_sec, 1.0)
    scale = 1.0 + (zoom_max_scale - 1.0) * progress  # 1.0 → 1.1
```

`scene_elapsed` でシーン開始からの経過を追う。
シーンが変わるたびに zoom が最初からやり直される。

## 合算ルールの設計判断

感情オフセットとアイドルアニメーションをどう合わせるかで一つ判断がある。

| 感情 | ルール | 理由 |
| --- | --- | --- |
| joy | bounce **のみ**（アイドルを止める） | 縦方向が二重になると動きすぎて不自然 |
| surprise | アイドル + shake を加算 | 縦（アイドル）と横（shake）で方向が違い干渉しない |
| thinking | アイドル + zoom_in を加算 | 揺れながら拡大しても自然に見える |

## 教訓

**既存の仕組みを流用できないか、先に考える。**

joy の bounce を実装するとき、最初は「新しい弾みアニメーションの関数が必要」と考えてしまいがち。
実際には ep3.4.3 で作った sin 波に振幅・周波数を変えるだけで実現できた。
「新しいものを作る前に、今あるものを使い回せないか」を確認するのが設計の第一歩。

感情ごとに**方向が違う**動きを割り当てることで、加算しても干渉しない設計になった。
これは偶然ではなく、各感情の「感じ」に合った方向を選んだ結果。
