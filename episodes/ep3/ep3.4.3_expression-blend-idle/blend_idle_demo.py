"""
ep3.4.3 サンプル: 表情補間（Expression Blend）+ アイドルアニメーション

Pillow だけで実装する2つの演出:

1. 表情補間（Expression Blend）
   口パク表情の切り替えをなめらかにする。
   Image.blend() で前フレームと現フレームを数フレームかけて混ぜる。

2. アイドルアニメーション（Idle Animation）
   キャラクターを正弦波で上下に揺らす。
   「何もしていない」ときも生きている感じを出す。

必要なもの:
  pip install Pillow

使い方:
  # 表情補間の比較フレームを生成（before / after PNG を出力）
  python blend_idle_demo.py blend --normal normal.png --open lipsync_open.png

  # アイドルアニメーション動画を生成（MP4 を出力）
  python blend_idle_demo.py idle --image normal.png

  # 両方まとめて生成
  python blend_idle_demo.py all --normal normal.png --open lipsync_open.png
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path


# ──────────────────────────────────────────────
# 1. 表情補間（Expression Blend）
# ──────────────────────────────────────────────

def blend_expressions(
    prev_img: "Image",
    curr_img: "Image",
    alpha: float,
) -> "Image":
    """前フレームと現フレームを alpha で線形補間して返す。

    alpha=0.0 → 完全に prev、alpha=1.0 → 完全に curr。
    Pillow の Image.blend() をそのまま薄くラップしたもの。

    Args:
        prev_img: 前の表情画像
        curr_img: 現在の表情画像
        alpha:    0.0〜1.0 の補間係数

    Returns:
        ブレンド済み画像
    """
    from PIL import Image
    if prev_img.size != curr_img.size:
        return curr_img  # サイズが違う場合はブレンド不可
    return Image.blend(prev_img, curr_img, alpha)


def generate_blend_comparison(
    normal_path: Path,
    open_path: Path,
    blend_frames: int = 3,
    fps: int = 30,
    output_dir: Path = Path("."),
) -> None:
    """表情補間の before / after 比較フレームを PNG として保存する。

    遷移開始の瞬間（alpha が最も目立つタイミング）を切り出して比較する。

    Args:
        normal_path:  口を閉じた表情画像のパス
        open_path:    口を大きく開いた表情画像のパス
        blend_frames: 補間フレーム数（0 = 瞬間カット）
        fps:          フレームレート（デフォルト 30fps）
        output_dir:   出力先ディレクトリ
    """
    from PIL import Image

    normal = Image.open(normal_path).convert("RGBA")
    open_img = Image.open(open_path).convert("RGBA")

    output_dir.mkdir(parents=True, exist_ok=True)

    if blend_frames == 0:
        # blend なし: 遷移が瞬間カットになる
        frame = open_img.copy()
        out = output_dir / "blend_before.png"
        frame.save(out)
        print(f"blend なし（瞬間カット）: {out}")
    else:
        # blend あり: 遷移中の中間フレームを生成
        blend_duration_sec = blend_frames / fps
        # 遷移開始から 1フレーム後のタイミング（補間の効果が最も見えるタイミング）
        elapsed = 1.0 / fps
        alpha = min(elapsed / blend_duration_sec, 1.0)
        frame = blend_expressions(normal, open_img, alpha)
        out = output_dir / "blend_after.png"
        frame.save(out)
        print(f"blend あり（alpha={alpha:.2f}）: {out}")


# ──────────────────────────────────────────────
# 2. アイドルアニメーション（Idle Animation）
# ──────────────────────────────────────────────

def calc_idle_offset_y(
    t: float,
    amplitude: float = 6.0,
    frequency: float = 0.4,
) -> int:
    """時刻 t におけるアバター Y 座標の正弦波オフセット（px）を返す。

    offset_y = amplitude × sin(2π × frequency × t)

    Args:
        t:          現在時刻（秒）
        amplitude:  振れ幅（px）。デフォルト 6px
        frequency:  周波数（Hz）。デフォルト 0.4Hz = 2.5秒に1往復

    Returns:
        Y 座標のオフセット値（整数 px）
    """
    if amplitude == 0 or frequency == 0:
        return 0
    return int(amplitude * math.sin(2 * math.pi * frequency * t))


def generate_idle_video(
    image_path: Path,
    duration_sec: float = 3.0,
    fps: int = 30,
    amplitude: float = 6.0,
    frequency: float = 0.4,
    canvas_size: tuple[int, int] = (400, 600),
    output_path: Path = Path("idle_demo.mp4"),
) -> None:
    """アイドルアニメーション動画を生成して MP4 として保存する。

    imageio[ffmpeg] が必要:
        pip install "imageio[ffmpeg]"

    キャラクター画像を正弦波で上下に揺らしたフレームを連結して動画にする。
    Y 座標の揺れ中心を amplitude 分だけ下にシフトし、
    上スイング時に画像上端が画面外に出ないようにする。

    Args:
        image_path:  アバター画像のパス（RGBA PNG 推奨）
        duration_sec: 動画の長さ（秒）
        fps:          フレームレート
        amplitude:    揺れ振幅（px）
        frequency:    揺れ周波数（Hz）
        canvas_size:  出力フレームサイズ（width, height）
        output_path:  出力 MP4 ファイルのパス
    """
    try:
        import imageio
        import numpy as np
    except ImportError:
        print("エラー: imageio が必要です。pip install 'imageio[ffmpeg]' を実行してください", file=sys.stderr)
        sys.exit(1)

    from PIL import Image

    avatar = Image.open(image_path).convert("RGBA")
    canvas_w, canvas_h = canvas_size

    # アバターをキャンバスサイズに収める（アスペクト比維持）
    scale = min(canvas_w / avatar.width, canvas_h / avatar.height)
    avatar = avatar.resize(
        (int(avatar.width * scale), int(avatar.height * scale)),
        Image.LANCZOS,
    )
    av_w, av_h = avatar.size

    # アバター基準位置: 水平中央・下端をキャンバス下端に揃える
    base_x = (canvas_w - av_w) // 2
    base_y = canvas_h - av_h

    total_frames = int(fps * duration_sec)
    frames = []

    for i in range(total_frames):
        t = i / fps
        offset_y = calc_idle_offset_y(t, amplitude=amplitude, frequency=frequency)

        # idle_margin: 上スイング最大（offset = -amplitude）のときに元の位置に戻るよう下にシフト
        idle_margin = int(amplitude)
        y = base_y + offset_y + idle_margin

        canvas = Image.new("RGBA", (canvas_w, canvas_h), (30, 30, 30, 255))
        canvas.paste(avatar, (base_x, y), avatar)

        frames.append(np.array(canvas.convert("RGB")))

        if (i + 1) % fps == 0:
            print(f"  {i + 1}/{total_frames} フレーム完了")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(str(output_path), frames, fps=fps, format="FFMPEG")
    print(f"保存完了: {output_path} ({output_path.stat().st_size:,} bytes)")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="表情補間・アイドルアニメーション デモ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # blend サブコマンド
    p_blend = sub.add_parser("blend", help="表情補間の before/after 比較フレームを生成")
    p_blend.add_argument("--normal", type=Path, required=True, help="口を閉じた表情画像（PNG）")
    p_blend.add_argument("--open",   type=Path, required=True, help="口を大きく開いた表情画像（PNG）")
    p_blend.add_argument("--frames", type=int, default=3, help="補間フレーム数（デフォルト: 3）")
    p_blend.add_argument("--out",    type=Path, default=Path("."), help="出力ディレクトリ（デフォルト: カレント）")

    # idle サブコマンド
    p_idle = sub.add_parser("idle", help="アイドルアニメーション動画を生成")
    p_idle.add_argument("--image",     type=Path, required=True, help="アバター画像（PNG）")
    p_idle.add_argument("--duration",  type=float, default=3.0,  help="動画の長さ（秒、デフォルト: 3.0）")
    p_idle.add_argument("--amplitude", type=float, default=6.0,  help="揺れ振幅 px（デフォルト: 6.0）")
    p_idle.add_argument("--frequency", type=float, default=0.4,  help="揺れ周波数 Hz（デフォルト: 0.4）")
    p_idle.add_argument("--out",       type=Path, default=Path("idle_demo.mp4"), help="出力 MP4 パス")

    # all サブコマンド
    p_all = sub.add_parser("all", help="blend と idle を両方生成")
    p_all.add_argument("--normal", type=Path, required=True, help="口を閉じた表情画像（PNG）")
    p_all.add_argument("--open",   type=Path, required=True, help="口を大きく開いた表情画像（PNG）")
    p_all.add_argument("--out",    type=Path, default=Path("."), help="出力ディレクトリ（デフォルト: カレント）")

    args = parser.parse_args()

    if args.command == "blend":
        print("=== blend なし（瞬間カット）===")
        generate_blend_comparison(args.normal, args.open, blend_frames=0, output_dir=args.out)
        print()
        print(f"=== blend あり（{args.frames} フレーム補間）===")
        generate_blend_comparison(args.normal, args.open, blend_frames=args.frames, output_dir=args.out)

    elif args.command == "idle":
        print(f"アイドルアニメーション: amplitude={args.amplitude}px, frequency={args.frequency}Hz")
        generate_idle_video(
            args.image,
            duration_sec=args.duration,
            amplitude=args.amplitude,
            frequency=args.frequency,
            output_path=args.out,
        )

    elif args.command == "all":
        print("=== 表情補間 ===")
        generate_blend_comparison(args.normal, args.open, blend_frames=0, output_dir=args.out)
        generate_blend_comparison(args.normal, args.open, blend_frames=3, output_dir=args.out)
        print()
        print("=== アイドルアニメーション ===")
        generate_idle_video(args.normal, output_path=args.out / "idle_demo.mp4")


if __name__ == "__main__":
    main()
