"""
Step 2: Pillowでアバターと背景を合成する

前提:
  pip install pillow
  透過PNG（アバター画像）を用意する

使い方:
  python step2_composite.py avatar.png
  → frame.png が生成される
"""

import sys

from PIL import Image

CANVAS_W, CANVAS_H = 1920, 1080
BG_COLOR = (18, 22, 36)       # 背景色（濃紺）
BAR_COLOR = (10, 14, 26, 200) # テロップバー色（半透明）
BAR_H = 170                   # テロップバーの高さ


def composite(avatar_path: str, output_path: str = "frame.png") -> None:
    # 背景を作成
    bg = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)

    # アバターを読み込んで中央下に配置
    avatar = Image.open(avatar_path).convert("RGBA")
    x = (CANVAS_W - avatar.width) // 2
    y = CANVAS_H - avatar.height - 20
    bg.paste(avatar, (x, y), avatar)  # 第3引数がマスク（透過を活かす）

    # テロップバー（半透明）を下部に重ねる
    bar = Image.new("RGBA", (CANVAS_W, BAR_H), BAR_COLOR)
    bg_rgba = bg.convert("RGBA")
    bg_rgba.alpha_composite(bar, dest=(0, CANVAS_H - BAR_H))

    bg_rgba.convert("RGB").save(output_path)
    print(f"完了: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python step2_composite.py <avatar.png>")
        sys.exit(1)
    composite(sys.argv[1])
