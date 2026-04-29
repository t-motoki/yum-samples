# 動画生成の高速化 — マルチプロセス化と VOICEVOX ロードバランシング

動画生成パイプラインが長尺動画で10分以上かかっていた問題に対して、
2つのアプローチで改善した記録です。

## 問題

動画生成パイプラインは主に2つのボトルネックがある。

1. **動画レンダリング（CPU バウンド）**: Pillow + MoviePy によるフレーム生成
2. **音声合成（I/O バウンド）**: VOICEVOX API へのリクエストがシーン数分だけ直列で走る

---

## 対策1: 動画生成処理を4プロセスへ移行

動画レンダリングは CPU バウンドなタスクのため、マルチプロセス化が有効。

Python の `multiprocessing` を使い、シーンを4プロセスに分割して並列レンダリングする。

```python
from multiprocessing import Pool

def render_scene(scene):
    # Pillow + MoviePy でシーンを動画クリップに変換
    ...

with Pool(processes=4) as pool:
    clips = pool.map(render_scene, scenes)
```

**注意点:**

- `Pool` は `if __name__ == "__main__":` ブロック内で起動する（Windows / macOS での二重起動防止）
- MoviePy のオブジェクトはプロセス間で共有できないため、各プロセスで独立して生成する
- 最終的な `concatenate_videoclips()` はシングルプロセスで行う（順序保証のため）

---

## 対策2: VOICEVOX マルチコンテナ + ロードバランサーで音声合成を並列化

VOICEVOX は1コンテナにつき同時リクエストを1つしか処理できない。
シーン数が多い動画では音声合成だけで数分かかる。

### 構成

```text
音声合成リクエスト
      ↓
 Nginx（ロードバランサー）
  ├── VOICEVOX コンテナ 1（:50021）
  ├── VOICEVOX コンテナ 2（:50022）
  ├── VOICEVOX コンテナ 3（:50023）
  └── VOICEVOX コンテナ 4（:50024）
```

### docker-compose の構成イメージ

```yaml
services:
  voicevox1:
    image: voicevox/voicevox_engine:cpu-ubuntu20.04-latest
    ports: ["50021:50021"]

  voicevox2:
    image: voicevox/voicevox_engine:cpu-ubuntu20.04-latest
    ports: ["50022:50021"]

  # voicevox3, voicevox4 も同様

  nginx:
    image: nginx:alpine
    ports: ["50100:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### nginx.conf（ラウンドロビン）

```nginx
upstream voicevox_cluster {
    server voicevox1:50021;
    server voicevox2:50021;
    server voicevox3:50021;
    server voicevox4:50021;
}

server {
    listen 80;
    location / {
        proxy_pass http://voicevox_cluster;
    }
}
```

アプリ側は `VOICEVOX_URL=http://localhost:50100` に向けるだけ。
コンテナ数を変えても、アプリコードの変更は不要。

---

## 結果

| 条件 | 改善前 | 改善後 |
| --- | --- | --- |
| 音声合成（20シーン） | 直列: 約4分 | 並列4台: 約1分 |
| 動画レンダリング | シングルプロセス: 約24分 | 4プロセス: 約6〜8分 |

---

## 教訓

- VOICEVOX は1コンテナ1リクエストの制約があるため、並列化はロードバランサーで行うのが素直
- 動画レンダリングは CPU バウンドなのでマルチプロセスが効く（マルチスレッドは GIL の影響で効果薄）
- ロードバランサーを挟むことで、コンテナ数を増減してもアプリ側の変更がゼロになる
