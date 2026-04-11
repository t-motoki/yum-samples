# ep2.1 同一キャラクターの表情だけを変える — 表情モーフィング再挑戦

動画「同一キャラクターの表情だけを変える — 表情モーフィング再挑戦」のサンプルコードです。

ep2.0 の失敗（IP-Adapter でキャラがブレる）を受けて、「変形」アプローチで再挑戦した記録です。

## この動画でやること

```
立ち絵（stand.png）→ THA3 で表情変形を試みる → 4段階の失敗 → Bing + rembg で別解
```

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `morph_expression.py` | THA3 で表情モーフィングを試みたコード（失敗実録） |
| `process_expression_images.py` | Bing 生成画像を rembg + Pillow で後処理する最終解法 |

---

## morph_expression.py（THA3 アプローチ・失敗）

### セットアップ

```bash
pip install talking-head-anime-3-demo torch pillow
```

モデルファイルを別途ダウンロードして `tha3_models/` に配置する必要があります。

- 手順: [THA3 GitHub](https://github.com/pkhungurn/talking-head-anime-3-demo) の "Downloading the Model" を参照
- サイズ: 約 1GB（Google Drive からダウンロード）
- ライセンス: コード MIT / モデル CC BY 4.0（作者: Pramook Khungurn）

### 使い方

```bash
python morph_expression.py avatar_rgba.png
```

入力画像は **背景なし・RGBA・512×512** の PNG が必要です（rembg で前処理してください）。

### なぜ失敗したか

| 失敗 | 原因 | 対処 |
| --- | --- | --- |
| ① 全画像が同じ出力 | sRGB→linear 変換の漏れ | THA3 ユーティリティの変換関数を使う |
| ② 表情の変化が見えない | 立ち絵が縦長で顔が画面の 1/3 しか占めない | 顔部分をクロップして拡大 |
| ③ 口が切れる | 透明パディング分だけクロップ位置がずれた | パディング除外後に再クロップ |
| ④ 顔ランドマーク誤認識 | ゆむの細い口・眉が標準ランドマークと一致しない | **THA3 での解決を断念** |

THA3 はアニメキャラ向けですが、キャラクターのスタイルによっては顔認識が機能しないケースがあります。

---

## process_expression_images.py（最終解法）

THA3 が対応できないと判明した時点で、アプローチを切り替えました。

**Bing Image Creator**（外部サービス）で表情別画像を生成し、コードで後処理して素材を揃えます。

> Bing Image Creator は Microsoft のクラウドサービスです。このチャンネルは基本的に無料 OSS のみで完結することを目指していますが、CPU 環境での制約上、ここだけ外部サービスを使用しています。

### セットアップ

```bash
pip install rembg pillow
```

### 使い方

```bash
# 個別に処理
python process_expression_images.py joy.png angry.png thinking.png

# ディレクトリをまとめて処理
python process_expression_images.py --dir input/ --output output/
```

出力は `340×720` の RGBA PNG（背景透明）で統一されます。
