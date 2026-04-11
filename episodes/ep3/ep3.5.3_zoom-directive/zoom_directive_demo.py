"""
ep3.5.3 サンプル: 汎用ズーム演出ディレクティブ

台本に1行書くだけでアバターをズームイン・ズームアウトできる仕組みのデモ。

  zoom_in:  clip_t=0 → 1.0x から始まり、duration 秒後に scale 倍に到達
  zoom_out: clip_t=0 → scale 倍から始まり、duration 秒後に 1.0x に戻る
  easing:   linear（均等変化）または ease_in_out（smoothstep: 始まりと終わりが滑らか）

設計の核心:
  - clip_t はクリップ先頭（0.0）からの時刻。シーンをまたいでもリセットされる
  - zoom ディレクティブは <!-- expression: --> や <!-- speaker: --> で自動リセット
  - thinking 表情の組み込みズームより優先される

必要なもの:
  pip install Pillow
  pip install "imageio[ffmpeg]"  # 動画出力する場合

使い方:
  # zoom in / zoom out の代表フレームを PNG として出力
  python zoom_directive_demo.py frames --image avatar.png

  # zoom in / zoom out の動画（3秒・30fps）を MP4 として出力
  python zoom_directive_demo.py video --image avatar.png

  # パラメータを変えて試す
  python zoom_directive_demo.py video --image avatar.png --scale 1.5 --duration 2.0 --easing linear
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Literal


# ──────────────────────────────────────────────
# ズーム計算
# ──────────────────────────────────────────────

Direction = Literal["in", "out"]
Easing = Literal["linear", "ease_in_out"]


def calc_zoom_scale(
    clip_t: float,
    direction: Direction = "in",
    scale: float = 1.3,
    duration: float = 1.0,
    easing: Easing = "ease_in_out",
) -> float:
    """clip_t（クリップ先頭からの経過秒数）から現在の拡大率を返す。

    Args:
        clip_t:    クリップ先頭（0.0）からの経過秒数
        direction: "in" = 拡大、"out" = 縮小
        scale:     目標倍率（1.0 以上）
        duration:  アニメーション完了までの秒数（0.0 = 瞬時切り替え）
        easing:    "linear" または "ease_in_out"（smoothstep）

    Returns:
        現在の拡大率（1.0 〜 scale の範囲）
    """
    if duration <= 0.0:
        progress = 1.0
    else:
        raw_progress = min(clip_t / duration, 1.0)
        if easing == "linear":
            progress = raw_progress
        else:
            # ease_in_out: smoothstep（3p^2 - 2p^3）
            p = raw_progress
            progress = 3 * p * p - 2 * p * p * p

    if direction == "in":
        result = 1.0 + (scale - 1.0) * progress
    else:  # "out"
        result = scale - (scale - 1.0) * progress

    return max(1.0, min(result, scale))


def calc_idle_offset_y(
    t: float,
    amplitude: float = 6.0,
    frequency: float = 0.4,
) -> int:
    """アイドルアニメーションの Y オフセット（px）を返す。"""
    if amplitude == 0 or frequency == 0:
        return 0
    return int(amplitude * math.sin(2 * math.pi * frequency * t))


# ──────────────────────────────────────────────
# フレーム描画
# ──────────────────────────────────────────────

def render_frame(
    avatar_img: "Image",
    canvas_size: tuple[int, int],
    scale: float,
    idle_offset_y: int,
    idle_margin: int,
    bg_color: tuple[int, int, int, int] = (30, 30, 30, 255),
) -> "Image":
    """1フレームを描画して返す。アバターは底辺揃えで配置する。"""
    from PIL import Image

    canvas_w, canvas_h = canvas_size
    canvas = Image.new("RGBA", canvas_size, bg_color)

    if scale != 1.0:
        new_w = int(avatar_img.width * scale)
        new_h = int(avatar_img.height * scale)
        av = avatar_img.resize((new_w, new_h), Image.LANCZOS)
    else:
        av = avatar_img

    # 底辺揃え: アバターの下端をキャンバス下端に合わせる
    base_x = (canvas_w - av.width) // 2
    base_y = canvas_h - av.height

    y = base_y + idle_offset_y + idle_margin
    canvas.paste(av, (base_x, y), av)
    return canvas


# ──────────────────────────────────────────────
# デモ生成
# ──────────────────────────────────────────────

DEMO_CASES: list[tuple[str, Direction, Easing]] = [
    ("zoom_in_ease",    "in",  "ease_in_out"),
    ("zoom_in_linear",  "in",  "linear"),
    ("zoom_out_ease",   "out", "ease_in_out"),
    ("zoom_out_linear", "out", "linear"),
]


def _prepare_avatar(image_path: Path, canvas_size: tuple[int, int]) -> "Image":
    from PIL import Image
    avatar = Image.open(image_path).convert("RGBA")
    canvas_w, canvas_h = canvas_size
    scale_fit = min(canvas_w / avatar.width, (canvas_h * 0.85) / avatar.height)
    return avatar.resize(
        (int(avatar.width * scale_fit), int(avatar.height * scale_fit)),
        Image.LANCZOS,
    )


def generate_frames(
    image_path: Path,
    output_dir: Path,
    scale: float,
    duration: float,
) -> None:
    """各パターンの中間フレーム（t = duration/2）を PNG として出力する。"""
    canvas_size = (400, 600)
    avatar = _prepare_avatar(image_path, canvas_size)
    idle_margin = 6  # アイドル振れ幅分の余白

    output_dir.mkdir(parents=True, exist_ok=True)
    t = duration / 2  # アニメーション途中のフレーム

    for name, direction, easing in DEMO_CASES:
        z = calc_zoom_scale(t, direction=direction, scale=scale, duration=duration, easing=easing)
        idle_y = calc_idle_offset_y(t)
        frame = render_frame(avatar, canvas_size, scale=z, idle_offset_y=idle_y, idle_margin=idle_margin)
        out = output_dir / f"{name}.png"
        frame.save(out)
        print(f"  {name:20s}: scale={z:.3f}  {out}")


def generate_video(
    image_path: Path,
    output_dir: Path,
    scale: float,
    duration: float,
    fps: int,
) -> None:
    """各パターンの動画を MP4 として出力する。"""
    try:
        import imageio
        import numpy as np
    except ImportError:
        print("エラー: imageio が必要です。pip install 'imageio[ffmpeg]' を実行してください", file=sys.stderr)
        sys.exit(1)

    canvas_size = (400, 600)
    avatar = _prepare_avatar(image_path, canvas_size)
    idle_margin = 6
    total_frames = int(fps * duration)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, direction, easing in DEMO_CASES:
        frames = []
        for i in range(total_frames):
            t = i / fps
            z = calc_zoom_scale(t, direction=direction, scale=scale, duration=duration, easing=easing)
            idle_y = calc_idle_offset_y(t)
            frame = render_frame(avatar, canvas_size, scale=z, idle_offset_y=idle_y, idle_margin=idle_margin)
            frames.append(np.array(frame.convert("RGB")))

        out = output_dir / f"{name}.mp4"
        imageio.mimsave(str(out), frames, fps=fps, format="FFMPEG")
        print(f"  {name:20s}: {out} ({out.stat().st_size:,} bytes)")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--image",    type=Path,  required=True, help="アバター画像（PNG）")
    p.add_argument("--out",      type=Path,  default=Path("."), help="出力ディレクトリ")
    p.add_argument("--scale",    type=float, default=1.3,   help="ズーム倍率（デフォルト: 1.3）")
    p.add_argument("--duration", type=float, default=1.5,   help="アニメーション秒数（デフォルト: 1.5）")
    p.add_argument("--easing",   choices=["linear", "ease_in_out"], default="ease_in_out",
                   help="イージング（デフォルト: ease_in_out）")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ズーム演出ディレクティブ デモ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_frames = sub.add_parser("frames", help="各パターンの代表フレーム（PNG）を出力")
    _add_common_args(p_frames)

    p_video = sub.add_parser("video", help="各パターンの動画（MP4）を出力")
    _add_common_args(p_video)
    p_video.add_argument("--fps", type=int, default=30, help="フレームレート（デフォルト: 30）")

    args = parser.parse_args()

    if args.command == "frames":
        print("代表フレームを生成中...")
        generate_frames(args.image, output_dir=args.out, scale=args.scale, duration=args.duration)
    elif args.command == "video":
        print("動画を生成中...")
        generate_video(args.image, output_dir=args.out, scale=args.scale, duration=args.duration, fps=args.fps)


if __name__ == "__main__":
    main()
