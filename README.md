# yum-samples

YouTubeチャンネル「ゆる系エンジニアの手記」で公開している動画のサンプルコードリポジトリです。

## このリポジトリについて

動画の中で実際に動かしているコードを、エピソードごとにフォルダに整理しています。
**すべて無料・OSS・Python だけで動きます。** 有料ツールや課金サービスは一切使いません。

チャンネルのコンセプトは「お金をかけずにソリューションを作る泥臭いプロセスをそのまま見せる」こと。
初級〜中級エンジニアの方が「自分でもできそう」と思えるコードを目指しています。

---

## エピソード一覧

| エピソード | タイトル | 主な技術 | フォルダ |
| --- | --- | --- | --- |
| ep0.0 | Pythonとフリーツールだけでアバターを無料で作る | rembg / Pillow | [ep0.0_avatar-creation](./episodes/ep0.0_avatar-creation/) |
| ep1.0 | アバターを動画に合成してナレーション付き動画を自動生成する | VOICEVOX / Pillow / MoviePy | [ep1.0_avatar-video-synthesis](./episodes/ep1.0_avatar-video-synthesis/) |
| ep2.0 | IP-Adapterで1枚のアバターから表情バリエーションを生成する（失敗実録） | IP-Adapter / Diffusers | [ep2.0_avatar-variant-generation](./episodes/ep2.0_avatar-variant-generation/) |
| ep2.1 | 同一キャラクターの表情だけを変える — 表情モーフィング再挑戦 | THA3 / rembg / Pillow | [ep2.1_avatar-expression-morphing](./episodes/ep2.1_avatar-expression-morphing/) |
| ep3.0 | 紙芝居スタイル動画パイプライン — 台本を書けばゆむが感情豊かに話す仕組みを作る | Pillow / VOICEVOX | [ep3.0_kamishibai-pipeline](./episodes/ep3.0_kamishibai-pipeline/) |
| ep3.1 | テロップフェードインアニメーション — 静止テロップに「動き」を加える | Pillow / MoviePy | [ep3.1_telop-animation](./episodes/ep3.1_telop-animation/) |
| ep2.2 | さばきゃん登場 — 聞いてくれる人がいるだけで、こんなに違う | Pillow（2キャラサムネイル）/ VOICEVOX | [ep2.2_sabacyan-introduction](./episodes/ep2.2_sabacyan-introduction/) |
| ep3.2 | BGMフェードイン・フェードアウト — 台本から音量曲線を制御する | MoviePy | [ep3.2_bgm-fade](./episodes/ep3.2_bgm-fade/) |

---

## 技術メモ

動画制作中に得た知見をまとめたノートです。コードより「考え方」が中心です。

| タイトル | 内容 |
| --- | --- |
| [動画生成の高速化](./notes/video-generation-speedup.md) | ImageClip / VideoClip の使い分けで生成時間を 27分 → 10分以内に改善 |

---

## セットアップ

- Python 3.11 以上が必要です（pyenv 推奨）
- 各エピソードの README に必要なライブラリとセットアップ手順が書いてあります
- 初めての方は [docs/setup.md](./docs/setup.md) を参照してください（WSL / Python / Docker の環境構築手順）

---

## 方針・制約

- 使用するライブラリはすべて **無料・OSS**
- メイン言語は **Python**
- 外部の有料 API・クラウド課金サービスは使わない
- 「動画を見て手元で再現できる」を最優先にする

---

## チャンネル

[ゆる系エンジニアの手記](https://www.youtube.com/channel/UCE1rHqZ5UvXkc0ZBLNiX6bA)

コードへの質問・フィードバックは Issue または動画のコメント欄でどうぞ。
