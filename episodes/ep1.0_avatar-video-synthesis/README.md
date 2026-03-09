# ep1.0 アバターを動画に合成してナレーション付き動画を自動生成する

動画「アバターを動画に合成してナレーション付き動画を自動生成する」のサンプルコードです。

## この動画でやること

VOICEVOX・Pillow・MoviePy の3つを組み合わせて、アバター付きのナレーション動画を自動生成します。

```
テキスト → [VOICEVOX] → 音声(.wav)
透過PNG  → [Pillow]   → フレーム画像(.png)
音声 + フレーム → [MoviePy] → 動画(.mp4)
```

## セットアップ

```bash
pip install pillow moviepy requests

# VOICEVOXをDockerで起動（Dockerが必要）
docker compose up -d voicevox
```

`docker-compose.yml` の内容：

```yaml
services:
  voicevox:
    image: voicevox/voicevox_engine:cpu-ubuntu20.04-latest
    ports:
      - "50021:50021"
```

## 使い方

3ステップで動画が生成できます。

```bash
# Step 1: 音声を生成
python step1_voicevox.py "こんにちは、ゆむです。"
# → output.wav

# Step 2: フレーム画像を合成（透過PNGのアバターが必要）
python step2_composite.py avatar.png
# → frame.png

# Step 3: 動画を生成
python step3_generate_video.py frame.png output.wav
# → output.mp4
```

## ポイント

- VOICEVOXのAPIは2段階：`audio_query` でパラメータ取得 → `synthesis` で音声生成
- Pillow の `paste(avatar, pos, avatar)` の第3引数がマスク。これがないと透過が効かない
- MoviePy の `with_duration(audio.duration)` で静止画の長さを音声に合わせる
