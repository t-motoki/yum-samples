"""
ep2.2 サンプル: 2キャラクターサムネイル生成デモ

さばきゃん登場回で実装した「2キャラクターを並べるサムネイルレイアウト」の
コアロジックをデモする。

必要なもの:
  pip install pillow
  2体のキャラクター画像（PNG、背景透過推奨）

使い方:
  python thumbnail_two_chars_demo.py --char1 yumu.png --char2 sabacyan.png
  python thumbnail_two_chars_demo.py  # サンプル画像で動作確認
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow が必要です: pip install pillow")
    sys.exit(1)

# サムネイルサイズ（YouTube 推奨）
W, H = 1280, 720

# 背景グラデーション（暗め）
BG_TOP    = (18, 22, 35)
BG_BOTTOM = (35, 42, 68)

# キャラクターレイアウト設定
#   target_h  : 画像の高さをこのサイズにリサイズ（縦基準）
#   x         : キャラクターの中心 X 座標
#   y_offset  : 下端からのオフセット（正 = 上にずらす）
#   mirror    : 左右反転（進行方向を内側に向けるため）
LAYOUT = {
    "char1": {"target_h": 400, "x": 230, "y_offset": 10, "mirror": True},   # 左・小さめ（サブ）
    "char2": {"target_h": 620, "x": 900, "y_offset": 10, "mirror": False},  # 右・大きめ（主役）
}


def make_gradient_bg(w: int, h: int, top: tuple, bottom: tuple) -> Image.Image:
    """縦方向グラデーション背景を生成する。"""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def load_and_resize(path: Path, target_h: int) -> Image.Image:
    """画像を高さ基準でリサイズし、RGBA に変換して返す。"""
    img = Image.open(path).convert("RGBA")
    ratio = target_h / img.height
    new_w = int(img.width * ratio)
    return img.resize((new_w, target_h), Image.LANCZOS)


def place_character(canvas: Image.Image, char_img: Image.Image, spec: dict) -> None:
    """キャラクター画像をレイアウト仕様に従ってキャンバスに貼り付ける。"""
    if spec["mirror"]:
        char_img = char_img.transpose(Image.FLIP_LEFT_RIGHT)

    target_h = char_img.height
    x = spec["x"] - char_img.width // 2        # 中心 X 基準
    y = H - target_h + spec["y_offset"]         # 下端基準

    # アルファチャンネルがある場合はマスク付きで合成
    if char_img.mode == "RGBA":
        canvas.paste(char_img, (x, y), mask=char_img.split()[3])
    else:
        canvas.paste(char_img, (x, y))


def draw_dummy_character(target_h: int, label: str, color: tuple) -> Image.Image:
    """画像ファイルがない場合のフォールバック: 色付き矩形でキャラクターを代替する。"""
    w = int(target_h * 0.6)
    img = Image.new("RGBA", (w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(10, 10), (w - 10, target_h - 10)], fill=(*color, 200))
    draw.text((w // 2, target_h // 2), label, fill=(255, 255, 255, 255), anchor="mm")
    return img


def generate_thumbnail(char1_path: Path | None, char2_path: Path | None) -> Image.Image:
    """2キャラクターサムネイルを生成して返す。"""
    canvas = make_gradient_bg(W, H, BG_TOP, BG_BOTTOM)

    # キャラクター1（左・サブ）
    spec1 = LAYOUT["char1"]
    if char1_path and char1_path.exists():
        img1 = load_and_resize(char1_path, spec1["target_h"])
    else:
        print(f"char1 画像が見つからないためダミーを使用: {char1_path}")
        img1 = draw_dummy_character(spec1["target_h"], "Char1", (80, 140, 200))
    place_character(canvas, img1, spec1)

    # キャラクター2（右・主役）
    spec2 = LAYOUT["char2"]
    if char2_path and char2_path.exists():
        img2 = load_and_resize(char2_path, spec2["target_h"])
    else:
        print(f"char2 画像が見つからないためダミーを使用: {char2_path}")
        img2 = draw_dummy_character(spec2["target_h"], "Char2", (200, 100, 140))
    place_character(canvas, img2, spec2)

    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description="2キャラクターサムネイル生成デモ")
    parser.add_argument("--char1", type=Path, default=None, help="キャラクター1の画像パス（PNG）")
    parser.add_argument("--char2", type=Path, default=None, help="キャラクター2の画像パス（PNG）")
    parser.add_argument("--output", type=Path, default=Path("output/thumbnail_demo.jpg"), help="出力先")
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    thumbnail = generate_thumbnail(args.char1, args.char2)
    thumbnail.convert("RGB").save(str(args.output), quality=95)
    print(f"生成完了: {args.output}")


if __name__ == "__main__":
    main()
