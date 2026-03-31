# ep3.5.6 PiP（ピクチャー・イン・ピクチャー）ディレクティブ

動画「台本に1行書くだけでスクリーン録画をアバターの隅に重ねられるようにした」のサンプルコードです。

台本に `<!-- pip: screen.mp4 -->` と1行書くだけで、スクリーン録画などの動画をアバターシーンの隅に
PiP（ピクチャー・イン・ピクチャー）として重ねて表示できる仕組みを実装しました。

## 使い方（台本）

```markdown
## シーン2: デモ開始

<!-- pip: inputs/episodes/ep3.6/screen_recording.mp4 position=bottom-right size=35% -->
ここからスクリーン録画を右下に表示しながら解説します。

## シーン3: 解説続き

pip ディレクティブを再度書かなくても、PiP はそのまま続きます。

## シーン4: 音声付きデモ

<!-- pip: inputs/episodes/ep3.6/demo.mp4 position=bottom-right size=35% pip_audio=true -->
別の pip を書くと上書きされます。pip_audio=true で PiP の音声もミックスされます。

## シーン5: デモ終了

<!-- pip: stop -->
ここから PiP が消えます。
```

## 仕組み

```
台本テキスト
    ↓ パーサーが <!-- pip: path [params] --> を読む
PipConfig(path, position, size_percent, loop, pip_audio)
    ↓ シーンをまたいで引き継がれる（<!-- pip: stop --> まで持続）
Scene.pip = PipConfig  ← 各シーンに PipConfig が付与される
    ↓ _build_pip_segments が連続区間をまとめる
[(PipConfig_A, 4.0s, 15.0s), (PipConfig_B, 15.0s, 20.0s)]
    ↓ _ffmpeg_pip_overlay が動画全体に後付けでオーバーレイ
ffmpeg overlay フィルターで PiP を合成した最終 MP4
```

BGM と同様に動画全体を1本の MP4 にしてから ffmpeg で後付けオーバーレイします。
これにより、シーン境界で PiP のタイムコードがリセットされず、連続再生されます。

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
| --- | --- | --- |
| `position` | `bottom-right` | PiP の表示位置（下記 9 種類を参照） |
| `size` | `30%` | PiP ウィンドウの幅（本編動画幅に対する割合。`%` 必須） |
| `loop` | `true` | `true`: PiP 動画をループ再生 / `false`: 最終フレームで静止 |
| `pip_audio` | `false` | `true`: PiP 動画の音声を本編音声にミックス |

## 利用可能な position 一覧（9種類）

| 値 | 位置 |
| --- | --- |
| `top-left` | 左上 |
| `top-right` | 右上 |
| `bottom-left` | 左下 |
| `bottom-right` | 右下（デフォルト） |
| `center` | 中央 |
| `center-top` | 上中央 |
| `center-bottom` | 下中央 |
| `left` | 左中央 |
| `right` | 右中央 |

## `dialogue_avatar_area` との組み合わせ

`dialogue` レイアウトで `position=right` の PiP と組み合わせる際は、
`dialogue_avatar_area=left` でキャラを左半分に寄せると「2人で鑑賞」の構図が作れます。

```markdown
<!-- config: layout=dialogue -->
<!-- config: dialogue_avatar_area=left -->
<!-- pip: screen_recording.mp4 position=right size=45% -->
キャラが画面左半分、スクリーン録画が画面右半分に表示されます。
```

| `dialogue_avatar_area` | 効果 |
| --- | --- |
| `full`（デフォルト） | キャラが画面全体の左右1/4 に配置される |
| `left` | キャラが左半分の左右1/4 に配置される（`position=right` の PiP と相性が良い） |
| `right` | キャラが右半分の左右1/4 に配置される |

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `pip_demo.py` | PipConfig・パーサー・_build_pip_segments・ffmpeg コマンド生成の全デモ |

## 動かし方

```bash
# 全デモを実行する（引数なし）
python pip_demo.py

# ディレクティブのパース結果を表示する
python pip_demo.py parse

# セグメント合成の概念を表示する（シーン → タイムライン変換 + ffmpeg コマンド）
python pip_demo.py segment
```

## 必要なもの

追加インストール不要（Python 標準ライブラリのみ）。
