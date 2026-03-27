"""
ep3.5.4 サンプル: カメラワーク演出（パン・Ken Burns・画面シェイク）

台本に1行書くだけでカメラワークを付けられる仕組みのデモ。

  pan:          フレーム全体を left/right/up/down に移動
  ken_burns:    ズーム（zoom_start → zoom_end）＋パン（pan_x/pan_y）を同時に動かす
  camera_shake: X・Y 二重サイン波でランダムに揺れる画面シェイク

設計の核心:
  - pan / ken_burns は scene_elapsed（セクション先頭からの累積時刻）で進行
  - camera_shake はシェイク開始クリップ先頭を 0 とした shake_elapsed を使う
    （scene_elapsed を使うと 2 クリップ目以降で duration を超えてシェイクが無効になる）
  - pan / shake は scale=1.0 のまま処理したいが、拡大なしではクロップ範囲が取れない
    → オフセット量に応じて最小 scale を自動確保し、拡大後にクロップして元サイズに戻す

必要なもの:
  pip install Pillow
  pip install "imageio[ffmpeg]"  # 動画出力する場合

使い方:
  # 代表フレームを PNG として出力
  python camera_work_demo.py frames --image avatar.png

  # 各演出の動画（3秒・30fps）を MP4 として出力
  python camera_work_demo.py video --image avatar.png

  # パラメータを変えて試す（pan）
  python camera_work_demo.py video --image avatar.png --demo pan_right --distance 150

  # パラメータを変えて試す（ken_burns）
  python camera_work_demo.py video --image avatar.png --demo ken_burns --zoom-start 1.0 --zoom-end 1.4
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Literal


# ──────────────────────────────────────────────
# 定数
# ──────────────────────────────────────────────

# camera_shake intensity ごとの最大振幅 (px)
SHAKE_AMPLITUDE: dict[str, int] = {"low": 4, "medium": 8, "high": 16}


# ──────────────────────────────────────────────
# カメラワーク計算
# ──────────────────────────────────────────────

Easing = Literal["linear", "ease_in_out"]


def _smoothstep(p: float) -> float:
    """ease_in_out: 3p^2 - 2p^3（始まりと終わりが滑らかな S 字曲線）"""
    return 3 * p * p - 2 * p * p * p


def _progress(elapsed: float, duration: float, easing: Easing) -> float:
    """経過時刻から [0.0, 1.0] の進行度を計算する。"""
    if duration <= 0.0:
        return 1.0
    raw = min(elapsed / duration, 1.0)
    return raw if easing == "linear" else _smoothstep(raw)


def calc_pan_offset(
    direction: str,
    distance: int,
    duration: float,
    scene_elapsed: float,
    easing: Easing = "ease_in_out",
) -> tuple[int, int]:
    """pan ディレクティブの (dx, dy) クロップオフセットを計算する。

    scene_elapsed=0 のとき (0, 0)。scene_elapsed >= duration のとき最大オフセット。

    座標系:
      left:  dx が負方向（コンテンツが右→左へ流れる）
      right: dx が正方向
      up:    dy が負方向
      down:  dy が正方向
    """
    p = _progress(scene_elapsed, duration, easing)
    d = int(distance * p)
    return {"left": (-d, 0), "right": (d, 0), "up": (0, -d), "down": (0, d)}[direction]


def calc_ken_burns(
    zoom_start: float,
    zoom_end: float,
    pan_x: int,
    pan_y: int,
    duration: float,
    scene_elapsed: float,
    easing: Easing = "ease_in_out",
) -> tuple[float, int, int]:
    """ken_burns ディレクティブの (scale, dx, dy) を計算する。

    ズームとパンが同一 progress で補間される。
    scene_elapsed=0 のとき (zoom_start, 0, 0)。
    """
    p = _progress(scene_elapsed, duration, easing)
    scale = zoom_start + (zoom_end - zoom_start) * p
    dx = int(pan_x * p)
    dy = int(pan_y * p)
    return (scale, dx, dy)


def calc_shake_offset(
    intensity: str,
    duration: float,
    shake_elapsed: float,
) -> tuple[int, int]:
    """camera_shake ディレクティブの (dx, dy) 揺れオフセットを計算する。

    duration 秒を超えた shake_elapsed では (0, 0) を返す（シェイク終了）。
    X/Y で異なる周波数のサイン波を重畳して「ランダムに見える揺れ」を作る。

    決定論的: 同一の (shake, shake_elapsed) では常に同じオフセットが返る（再現性保証）。
    """
    if shake_elapsed > duration:
        return (0, 0)
    amp = SHAKE_AMPLITUDE[intensity]
    # X: 13 Hz / Y: 17 Hz（非整数比率で単純な往復に見えにくくする）
    dx = int(amp * math.sin(2 * math.pi * 13.0 * shake_elapsed))
    dy = int(amp * math.sin(2 * math.pi * 17.0 * shake_elapsed))
    return (dx, dy)


# ──────────────────────────────────────────────
# フレーム描画
# ──────────────────────────────────────────────

def apply_camera_work(
    frame: "Image",
    scale: float = 1.0,
    pan_dx: int = 0,
    pan_dy: int = 0,
    shake_dx: int = 0,
    shake_dy: int = 0,
) -> "Image":
    """scale と (pan_dx, pan_dy, shake_dx, shake_dy) をフレームに適用する。

    処理の流れ:
      1. pan / shake のオフセットに必要な最小 scale を確保する
      2. 拡大してからクロップ → 元サイズに戻す
    """
    from PIL import Image

    w, h = frame.size
    total_dx = pan_dx + shake_dx
    total_dy = pan_dy + shake_dy

    if scale == 1.0 and total_dx == 0 and total_dy == 0:
        return frame

    # オフセット分だけ拡大する（クロップ範囲を確保するため）
    min_scale_x = 1.0 + abs(total_dx) / w if w > 0 else 1.0
    min_scale_y = 1.0 + abs(total_dy) / h if h > 0 else 1.0
    effective_scale = max(scale, min_scale_x, min_scale_y)

    new_w = int(w * effective_scale)
    new_h = int(h * effective_scale)
    enlarged = frame.resize((new_w, new_h), Image.LANCZOS)

    center_x = (new_w - w) // 2
    center_y = (new_h - h) // 2
    left = max(0, min(center_x + total_dx, new_w - w))
    top  = max(0, min(center_y + total_dy, new_h - h))

    return enlarged.crop((left, top, left + w, top + h))


def render_frame(
    avatar_img: "Image",
    canvas_size: tuple[int, int],
    scale: float,
    pan_dx: int,
    pan_dy: int,
    shake_dx: int,
    shake_dy: int,
    idle_offset_y: int = 0,
    bg_color: tuple[int, int, int, int] = (30, 30, 30, 255),
) -> "Image":
    """1フレームを描画して返す。アバターは底辺揃えで配置し、camera_work を適用する。"""
    from PIL import Image

    canvas_w, canvas_h = canvas_size
    canvas = Image.new("RGBA", canvas_size, bg_color)

    av = avatar_img
    base_x = (canvas_w - av.width) // 2
    base_y = canvas_h - av.height
    canvas.paste(av, (base_x, base_y + idle_offset_y), av)

    return apply_camera_work(canvas, scale=scale, pan_dx=pan_dx, pan_dy=pan_dy,
                             shake_dx=shake_dx, shake_dy=shake_dy)


def _prepare_avatar(image_path: Path, canvas_size: tuple[int, int]) -> "Image":
    from PIL import Image
    avatar = Image.open(image_path).convert("RGBA")
    canvas_w, canvas_h = canvas_size
    scale_fit = min(canvas_w / avatar.width, (canvas_h * 0.85) / avatar.height)
    return avatar.resize(
        (int(avatar.width * scale_fit), int(avatar.height * scale_fit)),
        Image.LANCZOS,
    )


# ──────────────────────────────────────────────
# デモケース定義
# ──────────────────────────────────────────────

def _build_demo_cases(args: argparse.Namespace) -> list[tuple[str, callable]]:
    """コマンドライン引数からデモケースのリストを返す。

    各ケースは (名前, scene_elapsed → (scale, pan_dx, pan_dy, shake_dx, shake_dy)) のタプル。
    """
    duration = args.duration

    def pan_case(direction: str) -> callable:
        def f(t: float) -> tuple:
            dx, dy = calc_pan_offset(direction, args.distance, duration, t)
            return (1.0, dx, dy, 0, 0)
        return f

    def ken_burns_case() -> callable:
        def f(t: float) -> tuple:
            scale, dx, dy = calc_ken_burns(
                args.zoom_start, args.zoom_end, args.pan_x, args.pan_y, duration, t
            )
            return (scale, dx, dy, 0, 0)
        return f

    def shake_case(intensity: str) -> callable:
        def f(t: float) -> tuple:
            dx, dy = calc_shake_offset(intensity, duration, t)
            return (1.0, 0, 0, dx, dy)
        return f

    all_cases = {
        "pan_left":       ("pan_left",       pan_case("left")),
        "pan_right":      ("pan_right",      pan_case("right")),
        "pan_up":         ("pan_up",         pan_case("up")),
        "pan_down":       ("pan_down",       pan_case("down")),
        "ken_burns":      ("ken_burns",      ken_burns_case()),
        "shake_low":      ("shake_low",      shake_case("low")),
        "shake_medium":   ("shake_medium",   shake_case("medium")),
        "shake_high":     ("shake_high",     shake_case("high")),
    }

    selected = getattr(args, "demo", "all")
    if selected == "all":
        return list(all_cases.values())
    if selected in all_cases:
        return [all_cases[selected]]
    print(f"エラー: 不明なデモ名 '{selected}'", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────
# 出力
# ──────────────────────────────────────────────

def generate_frames(image_path: Path, output_dir: Path, args: argparse.Namespace) -> None:
    """各デモの中間フレーム（t = duration/2）を PNG として出力する。"""
    canvas_size = (400, 600)
    avatar = _prepare_avatar(image_path, canvas_size)
    output_dir.mkdir(parents=True, exist_ok=True)
    t = args.duration / 2

    for name, calc in _build_demo_cases(args):
        scale, pan_dx, pan_dy, shake_dx, shake_dy = calc(t)
        idle_y = int(6 * math.sin(2 * math.pi * 0.4 * t))
        frame = render_frame(avatar, canvas_size, scale, pan_dx, pan_dy, shake_dx, shake_dy, idle_y)
        out = output_dir / f"{name}.png"
        frame.save(out)
        print(f"  {name:20s}: scale={scale:.3f}  pan=({pan_dx:+d},{pan_dy:+d})  shake=({shake_dx:+d},{shake_dy:+d})  {out}")


def generate_video(image_path: Path, output_dir: Path, args: argparse.Namespace) -> None:
    """各デモの動画を MP4 として出力する。"""
    try:
        import imageio
        import numpy as np
    except ImportError:
        print("エラー: imageio が必要です。pip install 'imageio[ffmpeg]' を実行してください", file=sys.stderr)
        sys.exit(1)

    canvas_size = (400, 600)
    avatar = _prepare_avatar(image_path, canvas_size)
    output_dir.mkdir(parents=True, exist_ok=True)
    total_frames = int(args.fps * args.duration)

    for name, calc in _build_demo_cases(args):
        frames = []
        for i in range(total_frames):
            t = i / args.fps
            scale, pan_dx, pan_dy, shake_dx, shake_dy = calc(t)
            idle_y = int(6 * math.sin(2 * math.pi * 0.4 * t))
            frame = render_frame(avatar, canvas_size, scale, pan_dx, pan_dy, shake_dx, shake_dy, idle_y)
            frames.append(np.array(frame.convert("RGB")))

        out = output_dir / f"{name}.mp4"
        imageio.mimsave(str(out), frames, fps=args.fps, format="FFMPEG")
        print(f"  {name:20s}: {out} ({out.stat().st_size:,} bytes)")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--image",      type=Path,  required=True, help="アバター画像（PNG）")
    p.add_argument("--out",        type=Path,  default=Path("."), help="出力ディレクトリ")
    p.add_argument("--duration",   type=float, default=2.0,   help="アニメーション秒数（デフォルト: 2.0）")
    p.add_argument("--demo",       type=str,   default="all",
                   help="実行するデモ名（all / pan_left / pan_right / pan_up / pan_down / ken_burns / shake_low / shake_medium / shake_high）")
    # pan パラメータ
    p.add_argument("--distance",   type=int,   default=100,   help="pan の移動量 px（デフォルト: 100）")
    # ken_burns パラメータ
    p.add_argument("--zoom-start", type=float, default=1.0,   dest="zoom_start", help="ken_burns 開始倍率（デフォルト: 1.0）")
    p.add_argument("--zoom-end",   type=float, default=1.3,   dest="zoom_end",   help="ken_burns 終了倍率（デフォルト: 1.3）")
    p.add_argument("--pan-x",      type=int,   default=40,    dest="pan_x",      help="ken_burns の X パン量 px（デフォルト: 40）")
    p.add_argument("--pan-y",      type=int,   default=20,    dest="pan_y",      help="ken_burns の Y パン量 px（デフォルト: 20）")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="カメラワーク演出デモ（pan / ken_burns / camera_shake）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_frames = sub.add_parser("frames", help="各デモの代表フレーム（PNG）を出力")
    _add_common_args(p_frames)

    p_video = sub.add_parser("video", help="各デモの動画（MP4）を出力")
    _add_common_args(p_video)
    p_video.add_argument("--fps", type=int, default=30, help="フレームレート（デフォルト: 30）")

    args = parser.parse_args()

    if args.command == "frames":
        print("代表フレームを生成中...")
        generate_frames(args.image, output_dir=args.out, args=args)
    elif args.command == "video":
        print("動画を生成中...")
        generate_video(args.image, output_dir=args.out, args=args)


if __name__ == "__main__":
    main()
