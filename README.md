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
| ep0.0 | Pythonとフリーツールだけでアバターを無料で作る | rembg / Pillow | [ep0.0_avatar-creation](./ep0.0_avatar-creation/) |
| ep1.0 | アバターを動画に合成してナレーション付き動画を自動生成する | VOICEVOX / Pillow / MoviePy | [ep1.0_avatar-video-synthesis](./ep1.0_avatar-video-synthesis/) |

---

## セットアップ

### 共通の前提

- Python 3.11 以上
- pip（Python 標準のパッケージ管理ツール）
- （ep1.0 のみ）Docker

### pip でのインストール

各エピソードフォルダ内の README に記載されているライブラリをインストールしてください。

```bash
# 例: ep0.0 の場合
pip install "rembg[cpu]" pillow

# 例: ep1.0 の場合
pip install pillow moviepy requests
```

### Docker を使う場合（ep1.0 のみ）

ep1.0 では VOICEVOX をローカルで動かすために Docker を使います。

```bash
docker compose up -d voicevox
```

使用する `docker-compose.yml` の内容は [ep1.0 の README](./ep1.0_avatar-video-synthesis/README.md) を参照してください。

---

## 方針・制約

- 使用するライブラリはすべて **無料・OSS**
- メイン言語は **Python**
- 外部の有料 API・クラウド課金サービスは使わない
- 「動画を見て手元で再現できる」を最優先にする

---

## チャンネル

コードへの質問・フィードバックは Issue または動画のコメント欄でどうぞ。
