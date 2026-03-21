"""
ep3.4.4 サンプル: 感情連動アニメーション（Emotion-Driven Action）

感情ラベル（joy / surprise / thinking / normal）に応じてアバターの動きが変わる仕組みのデモ。

  joy      → bounce: アイドルの2倍の振幅・周波数で上下に弾む
  surprise → shake:  フレームごとにランダムで左右に横揺れ
  thinking → zoom_in: scene_elapsed に応じて最大 1.1 倍まで線形に拡大する
  normal   → idle のみ（アイドルアニメーションだけ）

必要なもの:
  pip install Pillow
  pip install "imageio[ffmpeg]"  # 動画出力する場合

使い方:
  # 各感情の1フレームを PNG として出力
  python emotion_action_demo.py frames --image avatar.png

  # 各感情の動画（3秒・30fps）を MP4 として出力
  python emotion_action_demo.py video --image avatar.png

  # パラメータを変えて試す
  python emotion_action_demo.py video --image avatar.png --joy-amplitude 18.0 --surprise-amplitude 6
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path
from typing import Literal


# ──────────────────────────────────────────────
# アニメーション計算
# ──────────────────────────────────────────────

Emotion = Literal["joy", "surprise", "thinking", "normal"]


def calc_idle_offset_y(
    t: float,
    amplitude: float = 6.0,
    frequency: float = 0.4,
) -> int:
    """アイドルアニメーションの Y オフセット（px）を返す。

    amplitude=0 または frequency=0 のときは常に 0 を返す。

    Args:
        t:          現在時刻（秒）
        amplitude:  振れ幅（px）
        frequency:  周波数（Hz）。0.4Hz = 2.5秒で1往復

    Returns:
        Y 座標のオフセット（px）
    """
    if amplitude == 0 or frequency == 0:
        return 0
    return int(amplitude * math.sin(2 * math.pi * frequency * t))


def calc_emotion_offset(
    emotion: Emotion,
    t: float,
    scene_elapsed: float = 0.0,
    idle_amplitude: float = 6.0,
    idle_frequency: float = 0.4,
    joy_amplitude_ratio: float = 2.0,
    joy_frequency_ratio: float = 2.0,
    surprise_shake_amplitude: int = 3,
    zoom_duration_sec: float = 2.0,
    zoom_max_scale: float = 1.1,
) -> tuple[int, int, float]:
    """感情ラベルから (offset_x, offset_y, scale) を返す。

    joy / surprise / thinking / normal の4パターンに対応する。
    未知の感情ラベルは normal として扱う（何もしない）。

    - joy: アイドルより大きな振幅・周波数で上下に弾む。idle は置き換え。
    - surprise: フレームごとにランダムで左右に揺れる。
    - thinking: zoom_duration_sec 秒かけて zoom_max_scale まで線形に拡大する。
    - normal / 未知: 何もしない（idle オフセットは呼び出し元で加算）。

    Args:
        emotion:              感情ラベル
        t:                    現在時刻（秒）
        scene_elapsed:        シーン開始からの経過秒数（thinking zoom 計算用）
        idle_amplitude:       アイドル振れ幅 px
        idle_frequency:       アイドル周波数 Hz
        joy_amplitude_ratio:  joy 振幅 = idle_amplitude * ratio
        joy_frequency_ratio:  joy 周波数 = idle_frequency * ratio
        surprise_shake_amplitude: surprise の横揺れ幅 px（0 で無効）
        zoom_duration_sec:    thinking がフルスケールに達するまでの秒数
        zoom_max_scale:       thinking の最大拡大率

    Returns:
        (offset_x, offset_y, scale) のタプル
    """
    if emotion == "joy":
        joy_amplitude = idle_amplitude * joy_amplitude_ratio
        joy_frequency = idle_frequency * joy_frequency_ratio
        offset_y = int(joy_amplitude * math.sin(2 * math.pi * joy_frequency * t))
        return (0, offset_y, 1.0)

    elif emotion == "surprise":
        amp = surprise_shake_amplitude
        offset_x = random.choice([-amp, amp]) if amp != 0 else 0
        return (offset_x, 0, 1.0)

    elif emotion == "thinking":
        progress = min(scene_elapsed / zoom_duration_sec, 1.0) if zoom_duration_sec > 0 else 1.0
        scale = 1.0 + (zoom_max_scale - 1.0) * progress
        return (0, 0, scale)

    else:  # normal / 未知
        return (0, 0, 1.0)


# ──────────────────────────────────────────────
# フレーム描画
# ──────────────────────────────────────────────

def render_frame(
    avatar_img: "Image",
    canvas_size: tuple[int, int],
    offset_x: int,
    offset_y: int,
    idle_offset_y: int,
    scale: float,
    idle_margin: int,
    joy_margin: int,
    is_joy: bool,
    bg_color: tuple[int, int, int, int] = (30, 30, 30, 255),
) -> "Image":
    """1フレームを描画して返す。

    アバターを canvas に合わせてリサイズし、指定のオフセット・スケールで配置する。
    joy の場合はアイドルを止めて bounce に置き換える。

    Args:
        avatar_img:    アバター画像（RGBA）
        canvas_size:   (width, height)
        offset_x:      感情による X オフセット
        offset_y:      感情による Y オフセット（joy の場合はこれが bounce オフセット）
        idle_offset_y: アイドルアニメーション Y オフセット（joy の場合は使わない）
        scale:         拡大率（thinking zoom_in 用）
        idle_margin:   アイドル上スイング時に画面外に出ないようにするマージン
        joy_margin:    joy bounce 上スイング時のマージン
        is_joy:        joy ならアイドルを止めて bounce のみにする
        bg_color:      背景色 RGBA

    Returns:
        描画済みフレーム（RGBA Image）
    """
    from PIL import Image

    canvas_w, canvas_h = canvas_size
    canvas = Image.new("RGBA", canvas_size, bg_color)

    # スケール適用
    if scale != 1.0:
        new_w = int(avatar_img.width * scale)
        new_h = int(avatar_img.height * scale)
        av = avatar_img.resize((new_w, new_h), Image.LANCZOS)
    else:
        av = avatar_img

    # アバター基準位置（下端をキャンバス下端に揃え、水平中央）
    base_x = (canvas_w - av.width) // 2
    base_y = canvas_h - av.height

    # Y 位置の計算
    if is_joy:
        # joy: bounce のみ（アイドルは止める）
        y = base_y + offset_y + joy_margin
    else:
        # その他: アイドルに感情オフセットを加算
        y = base_y + idle_offset_y + offset_y + idle_margin

    x = base_x + offset_x

    canvas.paste(av, (x, y), av)
    return canvas


# ──────────────────────────────────────────────
# デモ生成
# ──────────────────────────────────────────────

EMOTIONS: list[Emotion] = ["normal", "joy", "surprise", "thinking"]


def generate_frames(
    image_path: Path,
    output_dir: Path = Path("."),
    canvas_size: tuple[int, int] = (400, 600),
    idle_amplitude: float = 6.0,
    idle_frequency: float = 0.4,
    joy_amplitude_ratio: float = 2.0,
    joy_frequency_ratio: float = 2.0,
    surprise_shake_amplitude: int = 3,
    zoom_duration_sec: float = 2.0,
    zoom_max_scale: float = 1.1,
) -> None:
    """各感情ラベルの代表フレームを PNG として出力する。

    t=0.5 秒時点のスナップショットを出力する（sin 波の波形が見えやすいタイミング）。
    """
    from PIL import Image

    avatar = Image.open(image_path).convert("RGBA")
    canvas_w, canvas_h = canvas_size
    scale_fit = min(canvas_w / avatar.width, canvas_h / avatar.height)
    avatar = avatar.resize(
        (int(avatar.width * scale_fit), int(avatar.height * scale_fit)),
        Image.LANCZOS,
    )

    idle_margin = int(idle_amplitude)
    joy_margin = int(idle_amplitude * joy_amplitude_ratio)

    output_dir.mkdir(parents=True, exist_ok=True)

    t = 0.5  # スナップショット時刻（秒）
    for emotion in EMOTIONS:
        offset_x, offset_y, scale = calc_emotion_offset(
            emotion, t, scene_elapsed=t,
            idle_amplitude=idle_amplitude,
            idle_frequency=idle_frequency,
            joy_amplitude_ratio=joy_amplitude_ratio,
            joy_frequency_ratio=joy_frequency_ratio,
            surprise_shake_amplitude=surprise_shake_amplitude,
            zoom_duration_sec=zoom_duration_sec,
            zoom_max_scale=zoom_max_scale,
        )
        idle_offset_y = calc_idle_offset_y(t, amplitude=idle_amplitude, frequency=idle_frequency)

        frame = render_frame(
            avatar, canvas_size,
            offset_x=offset_x, offset_y=offset_y,
            idle_offset_y=idle_offset_y, scale=scale,
            idle_margin=idle_margin, joy_margin=joy_margin,
            is_joy=(emotion == "joy"),
        )
        out = output_dir / f"emotion_{emotion}.png"
        frame.save(out)
        print(f"  {emotion:10s}: {out}")


def generate_video(
    image_path: Path,
    output_dir: Path = Path("."),
    duration_sec: float = 3.0,
    fps: int = 30,
    canvas_size: tuple[int, int] = (400, 600),
    idle_amplitude: float = 6.0,
    idle_frequency: float = 0.4,
    joy_amplitude_ratio: float = 2.0,
    joy_frequency_ratio: float = 2.0,
    surprise_shake_amplitude: int = 3,
    zoom_duration_sec: float = 2.0,
    zoom_max_scale: float = 1.1,
) -> None:
    """各感情ラベルの動画を MP4 として出力する（感情ごとに1ファイル）。"""
    try:
        import imageio
        import numpy as np
    except ImportError:
        print("エラー: imageio が必要です。pip install 'imageio[ffmpeg]' を実行してください", file=sys.stderr)
        sys.exit(1)

    from PIL import Image

    avatar = Image.open(image_path).convert("RGBA")
    canvas_w, canvas_h = canvas_size
    scale_fit = min(canvas_w / avatar.width, canvas_h / avatar.height)
    avatar = avatar.resize(
        (int(avatar.width * scale_fit), int(avatar.height * scale_fit)),
        Image.LANCZOS,
    )

    idle_margin = int(idle_amplitude)
    joy_margin = int(idle_amplitude * joy_amplitude_ratio)
    total_frames = int(fps * duration_sec)

    output_dir.mkdir(parents=True, exist_ok=True)

    for emotion in EMOTIONS:
        frames = []
        for i in range(total_frames):
            t = i / fps
            offset_x, offset_y, scale = calc_emotion_offset(
                emotion, t, scene_elapsed=t,
                idle_amplitude=idle_amplitude,
                idle_frequency=idle_frequency,
                joy_amplitude_ratio=joy_amplitude_ratio,
                joy_frequency_ratio=joy_frequency_ratio,
                surprise_shake_amplitude=surprise_shake_amplitude,
                zoom_duration_sec=zoom_duration_sec,
                zoom_max_scale=zoom_max_scale,
            )
            idle_offset_y = calc_idle_offset_y(t, amplitude=idle_amplitude, frequency=idle_frequency)

            frame = render_frame(
                avatar, canvas_size,
                offset_x=offset_x, offset_y=offset_y,
                idle_offset_y=idle_offset_y, scale=scale,
                idle_margin=idle_margin, joy_margin=joy_margin,
                is_joy=(emotion == "joy"),
            )
            frames.append(np.array(frame.convert("RGB")))

        out = output_dir / f"emotion_{emotion}.mp4"
        imageio.mimsave(str(out), frames, fps=fps, format="FFMPEG")
        print(f"  {emotion:10s}: {out} ({out.stat().st_size:,} bytes)")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--image",              type=Path,  required=True,  help="アバター画像（PNG）")
    p.add_argument("--out",                type=Path,  default=Path("."), help="出力ディレクトリ")
    p.add_argument("--idle-amplitude",     type=float, default=6.0,    help="アイドル振れ幅 px（デフォルト: 6.0）")
    p.add_argument("--idle-frequency",     type=float, default=0.4,    help="アイドル周波数 Hz（デフォルト: 0.4）")
    p.add_argument("--joy-amplitude",      type=float, default=2.0,    help="joy 振幅倍率（デフォルト: 2.0 = idle の2倍）")
    p.add_argument("--joy-frequency",      type=float, default=2.0,    help="joy 周波数倍率（デフォルト: 2.0 = idle の2倍）")
    p.add_argument("--surprise-amplitude", type=int,   default=3,      help="surprise 横揺れ幅 px（デフォルト: 3）")
    p.add_argument("--zoom-duration",      type=float, default=2.0,    help="thinking zoom 完了までの秒数（デフォルト: 2.0）")
    p.add_argument("--zoom-max-scale",     type=float, default=1.1,    help="thinking 最大拡大率（デフォルト: 1.1）")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="感情連動アニメーション デモ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_frames = sub.add_parser("frames", help="各感情の代表フレーム（PNG）を出力")
    _add_common_args(p_frames)

    p_video = sub.add_parser("video", help="各感情の動画（MP4）を出力")
    _add_common_args(p_video)
    p_video.add_argument("--duration", type=float, default=3.0, help="動画の長さ（秒、デフォルト: 3.0）")

    args = parser.parse_args()

    kwargs = dict(
        idle_amplitude=args.idle_amplitude,
        idle_frequency=args.idle_frequency,
        joy_amplitude_ratio=args.joy_amplitude,
        joy_frequency_ratio=args.joy_frequency,
        surprise_shake_amplitude=args.surprise_amplitude,
        zoom_duration_sec=args.zoom_duration,
        zoom_max_scale=args.zoom_max_scale,
    )

    if args.command == "frames":
        print("各感情の代表フレームを生成中...")
        generate_frames(args.image, output_dir=args.out, **kwargs)
    elif args.command == "video":
        print("各感情の動画を生成中...")
        generate_video(args.image, output_dir=args.out, duration_sec=args.duration, **kwargs)


if __name__ == "__main__":
    main()
