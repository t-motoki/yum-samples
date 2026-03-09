# ep01 アバターの背景除去

動画「Pythonとフリーツールだけでアバターを無料で作る」のサンプルコードです。

## やること

`rembg` を使ってアバター画像の背景を除去します。
`isnet-anime` モデルを使うことで、アニメ調のイラストをきれいに切り抜けます。

## セットアップ

```bash
pip install "rembg[cpu]" pillow
```

## 使い方

```bash
python remove_bg.py avatar.jpg
# → avatar_nobg.png が生成される
```

## ポイント

- モデルに `isnet-anime` を指定するのがコツ（デフォルトより精度が上がる）
- 出力は背景が透明な PNG になる
