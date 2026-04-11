"""
Bing Image Creator で生成した表情画像を rembg + Pillow で後処理する（最終的な解法）

動画「同一キャラクターの表情だけを変える — 表情モーフィング再挑戦」で
最終的に採用したアプローチのサンプルです。

THA3 がゆむの立ち絵に対応できなかったため、
Bing Image Creator（外部サービス）で表情別の画像を生成し、
rembg で背景除去 → Pillow でリサイズ統一、という流れで素材を揃えました。

前提:
  pip install rembg pillow

使い方:
  python process_expression_images.py input/joy.png input/angry.png input/thinking.png
  → output/ に処理済みの joy.png, angry.png, thinking.png が生成される

  または input/ ディレクトリをまとめて処理:
  python process_expression_images.py --dir input/
"""

import argparse
import sys
from pathlib import Path

from PIL import Image
from rembg import remove

# 出力サイズ（動画フレームに合わせた縦長サイズ）
OUTPUT_WIDTH = 340
OUTPUT_HEIGHT = 720


def process(src: Path, dst: Path) -> None:
    """1枚の画像に背景除去・リサイズ統一を適用して保存する"""
    print(f"処理中: {src.name} ...")

    with open(src, "rb") as f:
        result_bytes = remove(f.read())

    img = Image.open(__import__("io").BytesIO(result_bytes)).convert("RGBA")

    # アスペクト比を保ちながら OUTPUT_WIDTH に合わせてリサイズ
    orig_w, orig_h = img.size
    scale = OUTPUT_WIDTH / orig_w
    new_h = int(orig_h * scale)
    img = img.resize((OUTPUT_WIDTH, new_h), Image.LANCZOS)

    # OUTPUT_HEIGHT に満たない場合は上端を基準にパディング
    canvas = Image.new("RGBA", (OUTPUT_WIDTH, OUTPUT_HEIGHT), (0, 0, 0, 0))
    canvas.paste(img, (0, 0))

    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)
    print(f"  → {dst}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", help="処理する画像ファイル")
    parser.add_argument("--dir", help="ディレクトリ内の PNG をまとめて処理")
    parser.add_argument("--output", default="output", help="出力先ディレクトリ（デフォルト: output）")
    args = parser.parse_args()

    out = Path(args.output)
    targets: list[Path] = []

    if args.dir:
        targets = sorted(Path(args.dir).glob("*.png"))
    elif args.files:
        targets = [Path(f) for f in args.files]
    else:
        parser.print_help()
        sys.exit(1)

    if not targets:
        print("処理対象の PNG が見つかりませんでした")
        sys.exit(1)

    for src in targets:
        process(src, out / src.name)

    print(f"\n完了: {len(targets)} 枚を {out}/ に保存しました")


if __name__ == "__main__":
    main()
