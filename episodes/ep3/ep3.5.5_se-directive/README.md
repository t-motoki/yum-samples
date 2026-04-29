# ep3.5.5 SE（効果音）ディレクティブ

動画「台本に1行書くだけで効果音を鳴らせるようにした」のサンプルコードです。

台本に `<!-- se: プリセット名 -->` と1行書くだけで効果音を鳴らせる仕組みを実装しました。

## 使い方（台本）

```markdown
<!-- se: ひらめく1 -->
台本に1行書くだけで、効果音が鳴るようにしました。

<!-- se: スイッチを押す offset=1.5 -->
「offset=1.5」と書くと、シーン開始から1.5秒後に鳴ります。
```

## 仕組み

```
台本テキスト
    ↓ パーサーが <!-- se: xxx --> を読む
SECue(preset="ひらめく1", offset=0.0)
    ↓ SEPresetResolver がファイルパスに変換
src/assets/se/ひらめく1.mp3
    ↓ AudioFileClip.with_start(offset) で配置
CompositeAudioClip([narration, se_audio])  ← ミックス完了
```

BGM とは独立したフローで処理するため、BGM 音量を変えても SE のタイミングは変わりません。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `se_demo.py` | SE パーサー・SEPresetResolver・ミックス処理の全デモ |

## 動かし方

```bash
# SE ディレクティブのパース動作を確認する（音声ファイル不要）
python se_demo.py parse

# 利用可能なプリセット一覧を表示する（youtuber-yum リポジトリのルートから実行）
python se_demo.py list

# ナレーション音声 + SE をミックスして出力する
python se_demo.py mix --narration narration.wav --se src/assets/se/ひらめく1.mp3

# offset 付きでミックスする
python se_demo.py mix --narration narration.wav --se src/assets/se/スイッチを押す.mp3 --offset 1.5

# 複数の SE をミックスする
python se_demo.py mix \
  --narration narration.wav \
  --se src/assets/se/ひらめく1.mp3 \
  --se src/assets/se/きらきら輝く3.mp3 \
  --offset 0 2.0
```

## 必要なもの

```
pip install moviepy
```
