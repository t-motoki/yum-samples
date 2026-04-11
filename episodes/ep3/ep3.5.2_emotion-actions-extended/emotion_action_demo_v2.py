"""
ep3.5.2 サンプル: 感情アクション拡張（5種追加）

ep3.4.4 の3種（joy / surprise / thinking）に加えて、
5種類の感情アクションを追加したバージョン。

  angry    → 激しい横揺れ（surprise の2倍以上の振れ幅・速い周期）
  sad      → ゆっくり下へ沈む（scene_elapsed に比例・最大値でクランプ）
  smile    → 穏やかな縦揺れ（joy と同系・振れ幅と周波数を抑えて落ち着かせる）
  troubled → 小刻みな縦揺れ（高周波・小振幅・不安感）
  chibi    → 素早い小刻みバウンス（高周波・小振幅・かわいらしい弾み）

全8種を含む完全版:
  normal / joy / surprise / thinking / angry / sad / smile / troubled / chibi

設計の共通ルール:
  - joy / smile は「アイドルを置き換える」（縦方向が被るので加算すると揺れすぎる）
  - angry / troubled / chibi は「アイドルに加算する」（方向が干渉しないか無視できる差）
  - sad は「scene_elapsed に依存」（怒り・喜びと違い時間経過で変化する感情）

必要なもの:
  pip install Pillow
  pip install "imageio[ffmpeg]"  # 動画出力する場合

使い方:
  # 各感情の1フレームを PNG として出力
  python emotion_action_demo_v2.py frames --image avatar.png

  # 各感情の動画（3秒・30fps）を MP4 として出力
  python emotion_action_demo_v2.py video --image avatar.png

  # パラメータを変えて試す
  python emotion_action_demo_v2.py video --image avatar.png --angry-amplitude 12 --sad-max-px 30
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

Emotion = Literal[
    "joy", "surprise", "thinking",
    "angry", "sad", "smile", "troubled", "chibi",
    "normal",
]


def calc_idle_offset_y(
    t: float,
    amplitude: float = 6.0,
    frequency: float = 0.4,
) -> int:
    """アイドルアニメーションの Y オフセット（px）を返す。"""
    if amplitude == 0 or frequency == 0:
        return 0
    return int(amplitude * math.sin(2 * math.pi * frequency * t))


def calc_emotion_offset(
    emotion: Emotion,
    t: float,
    scene_elapsed: float = 0.0,
    # アイドル
    idle_amplitude: float = 6.0,
    idle_frequency: float = 0.4,
    # joy / smile（縦揺れ系・idle 置き換え）
    joy_amplitude_ratio: float = 2.0,
    joy_frequency_ratio: float = 2.0,
    smile_amplitude_ratio: float = 1.0,
    smile_frequency_ratio: float = 1.0,
    # surprise / angry（横揺れ系）
    surprise_shake_amplitude: int = 3,
    angry_shake_amplitude: int = 8,
    # sad（沈む系）
    sad_sink_max_px: int = 20,
    sad_sink_duration_sec: float = 3.0,
    sad_wave_amplitude: int = 2,
    sad_wave_frequency: float = 0.5,
    # troubled / chibi（縦揺れ・idle に加算）
    troubled_amplitude: int = 4,
    troubled_frequency: float = 2.0,
    chibi_amplitude: int = 5,
    chibi_frequency: float = 3.0,
    # thinking（ズーム）
    zoom_duration_sec: float = 2.0,
    zoom_max_scale: float = 1.1,
) -> tuple[int, int, float]:
    """感情ラベルから (offset_x, offset_y, scale) を返す。

    返り値:
        (offset_x, offset_y, scale)
        - offset_x: 水平方向のオフセット（px）。正 = 右
        - offset_y: 垂直方向のオフセット（px）。正 = 下
        - scale: 拡大率（1.0 = 等倍）

    加算ルール（呼び出し元で適用）:
        joy / smile の場合: bounce のみ（アイドルは止める）
        その他の場合     : アイドル + 感情オフセットを加算
    """
    if emotion in ("joy", "smile"):
        # idle を置き換える縦揺れ系
        ratio_a = joy_amplitude_ratio if emotion == "joy" else smile_amplitude_ratio
        ratio_f = joy_frequency_ratio if emotion == "joy" else smile_frequency_ratio
        amp = idle_amplitude * ratio_a
        freq = idle_frequency * ratio_f
        offset_y = int(amp * math.sin(2 * math.pi * freq * t))
        return (0, offset_y, 1.0)

    elif emotion == "surprise":
        amp = surprise_shake_amplitude
        offset_x = random.choice([-amp, amp]) if amp != 0 else 0
        return (offset_x, 0, 1.0)

    elif emotion == "angry":
        amp = angry_shake_amplitude
        offset_x = random.choice([-amp, amp]) if amp != 0 else 0
        return (offset_x, 0, 1.0)

    elif emotion == "sad":
        # scene_elapsed に比例して下へ沈む（最大 sad_sink_max_px でクランプ）
        elapsed = max(scene_elapsed, 0.0)
        sink = (elapsed / sad_sink_duration_sec) * sad_sink_max_px if sad_sink_duration_sec > 0 else sad_sink_max_px
        wave = sad_wave_amplitude * math.sin(2 * math.pi * sad_wave_frequency * elapsed)
        total_dy = min(sink + wave, sad_sink_max_px)
        return (0, int(total_dy), 1.0)

    elif emotion == "troubled":
        # 小刻みな縦揺れ（idle に加算）
        offset_y = int(troubled_amplitude * math.sin(2 * math.pi * troubled_frequency * scene_elapsed))
        return (0, offset_y, 1.0)

    elif emotion == "chibi":
        # 素早い小刻みバウンス（idle に加算）
        offset_y = int(chibi_amplitude * math.sin(2 * math.pi * chibi_frequency * scene_elapsed))
        return (0, offset_y, 1.0)

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
    bounce_margin: int,
    replace_idle: bool,
    bg_color: tuple[int, int, int, int] = (30, 30, 30, 255),
) -> "Image":
    """1フレームを描画して返す。

    Args:
        replace_idle: True のとき idle を止めて bounce のみにする（joy / smile 用）
    """
    from PIL import Image

    canvas_w, canvas_h = canvas_size
    canvas = Image.new("RGBA", canvas_size, bg_color)

    if scale != 1.0:
        new_w = int(avatar_img.width * scale)
        new_h = int(avatar_img.height * scale)
        av = avatar_img.resize((new_w, new_h), Image.LANCZOS)
    else:
        av = avatar_img

    base_x = (canvas_w - av.width) // 2
    base_y = canvas_h - av.height

    if replace_idle:
        y = base_y + offset_y + bounce_margin
    else:
        y = base_y + idle_offset_y + offset_y + idle_margin

    x = base_x + offset_x
    canvas.paste(av, (x, y), av)
    return canvas


# ──────────────────────────────────────────────
# デモ生成
# ──────────────────────────────────────────────

EMOTIONS: list[Emotion] = [
    "normal", "joy", "surprise", "thinking",
    "angry", "sad", "smile", "troubled", "chibi",
]


def _build_kwargs(args: argparse.Namespace) -> dict:
    return dict(
        idle_amplitude=args.idle_amplitude,
        idle_frequency=args.idle_frequency,
        joy_amplitude_ratio=args.joy_amplitude,
        joy_frequency_ratio=args.joy_frequency,
        smile_amplitude_ratio=args.smile_amplitude,
        smile_frequency_ratio=args.smile_frequency,
        surprise_shake_amplitude=args.surprise_amplitude,
        angry_shake_amplitude=args.angry_amplitude,
        sad_sink_max_px=args.sad_max_px,
        sad_sink_duration_sec=args.sad_duration,
        sad_wave_amplitude=args.sad_wave_amplitude,
        sad_wave_frequency=args.sad_wave_frequency,
        troubled_amplitude=args.troubled_amplitude,
        troubled_frequency=args.troubled_frequency,
        chibi_amplitude=args.chibi_amplitude,
        chibi_frequency=args.chibi_frequency,
        zoom_duration_sec=args.zoom_duration,
        zoom_max_scale=args.zoom_max_scale,
    )


def generate_frames(image_path: Path, output_dir: Path, kwargs: dict) -> None:
    """各感情ラベルの代表フレームを PNG として出力する（t=0.5 秒のスナップショット）。"""
    from PIL import Image

    avatar = Image.open(image_path).convert("RGBA")
    canvas_size = (400, 600)
    canvas_w, canvas_h = canvas_size
    scale_fit = min(canvas_w / avatar.width, canvas_h / avatar.height)
    avatar = avatar.resize(
        (int(avatar.width * scale_fit), int(avatar.height * scale_fit)),
        Image.LANCZOS,
    )

    idle_amplitude = kwargs["idle_amplitude"]
    idle_frequency = kwargs["idle_frequency"]
    idle_margin = int(idle_amplitude)
    bounce_margin = int(idle_amplitude * kwargs["joy_amplitude_ratio"])
    output_dir.mkdir(parents=True, exist_ok=True)

    t = 0.5
    for emotion in EMOTIONS:
        offset_x, offset_y, scale = calc_emotion_offset(emotion, t, scene_elapsed=t, **kwargs)
        idle_offset_y = calc_idle_offset_y(t, amplitude=idle_amplitude, frequency=idle_frequency)
        replace_idle = emotion in ("joy", "smile")

        frame = render_frame(
            avatar, canvas_size,
            offset_x=offset_x, offset_y=offset_y,
            idle_offset_y=idle_offset_y, scale=scale,
            idle_margin=idle_margin, bounce_margin=bounce_margin,
            replace_idle=replace_idle,
        )
        out = output_dir / f"emotion_{emotion}.png"
        frame.save(out)
        print(f"  {emotion:10s}: {out}")


def generate_video(image_path: Path, output_dir: Path, duration_sec: float, fps: int, kwargs: dict) -> None:
    """各感情ラベルの動画を MP4 として出力する（感情ごとに1ファイル）。"""
    try:
        import imageio
        import numpy as np
    except ImportError:
        print("エラー: imageio が必要です。pip install 'imageio[ffmpeg]' を実行してください", file=sys.stderr)
        sys.exit(1)

    from PIL import Image

    avatar = Image.open(image_path).convert("RGBA")
    canvas_size = (400, 600)
    canvas_w, canvas_h = canvas_size
    scale_fit = min(canvas_w / avatar.width, canvas_h / avatar.height)
    avatar = avatar.resize(
        (int(avatar.width * scale_fit), int(avatar.height * scale_fit)),
        Image.LANCZOS,
    )

    idle_amplitude = kwargs["idle_amplitude"]
    idle_frequency = kwargs["idle_frequency"]
    idle_margin = int(idle_amplitude)
    bounce_margin = int(idle_amplitude * kwargs["joy_amplitude_ratio"])
    total_frames = int(fps * duration_sec)
    output_dir.mkdir(parents=True, exist_ok=True)

    for emotion in EMOTIONS:
        frames = []
        for i in range(total_frames):
            t = i / fps
            offset_x, offset_y, scale = calc_emotion_offset(emotion, t, scene_elapsed=t, **kwargs)
            idle_offset_y = calc_idle_offset_y(t, amplitude=idle_amplitude, frequency=idle_frequency)
            replace_idle = emotion in ("joy", "smile")

            frame = render_frame(
                avatar, canvas_size,
                offset_x=offset_x, offset_y=offset_y,
                idle_offset_y=idle_offset_y, scale=scale,
                idle_margin=idle_margin, bounce_margin=bounce_margin,
                replace_idle=replace_idle,
            )
            frames.append(np.array(frame.convert("RGB")))

        out = output_dir / f"emotion_{emotion}.mp4"
        imageio.mimsave(str(out), frames, fps=fps, format="FFMPEG")
        print(f"  {emotion:10s}: {out} ({out.stat().st_size:,} bytes)")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def _add_common_args(p: argparse.ArgumentParser) -> None:
    # アイドル
    p.add_argument("--image",               type=Path,  required=True,  help="アバター画像（PNG）")
    p.add_argument("--out",                 type=Path,  default=Path("."), help="出力ディレクトリ")
    p.add_argument("--idle-amplitude",      type=float, default=6.0,    help="アイドル振れ幅 px（デフォルト: 6.0）")
    p.add_argument("--idle-frequency",      type=float, default=0.4,    help="アイドル周波数 Hz（デフォルト: 0.4）")
    # joy / smile
    p.add_argument("--joy-amplitude",       type=float, default=2.0,    help="joy 振幅倍率（デフォルト: 2.0）")
    p.add_argument("--joy-frequency",       type=float, default=2.0,    help="joy 周波数倍率（デフォルト: 2.0）")
    p.add_argument("--smile-amplitude",     type=float, default=1.0,    help="smile 振幅倍率（デフォルト: 1.0）")
    p.add_argument("--smile-frequency",     type=float, default=1.0,    help="smile 周波数倍率（デフォルト: 1.0）")
    # surprise / angry
    p.add_argument("--surprise-amplitude",  type=int,   default=3,      help="surprise 横揺れ幅 px（デフォルト: 3）")
    p.add_argument("--angry-amplitude",     type=int,   default=8,      help="angry 横揺れ幅 px（デフォルト: 8）")
    # sad
    p.add_argument("--sad-max-px",          type=int,   default=20,     help="sad 最大沈み量 px（デフォルト: 20）")
    p.add_argument("--sad-duration",        type=float, default=3.0,    help="sad がフル沈みに達するまでの秒数（デフォルト: 3.0）")
    p.add_argument("--sad-wave-amplitude",  type=int,   default=2,      help="sad の微小波 振れ幅 px（デフォルト: 2）")
    p.add_argument("--sad-wave-frequency",  type=float, default=0.5,    help="sad の微小波 周波数 Hz（デフォルト: 0.5）")
    # troubled / chibi
    p.add_argument("--troubled-amplitude",  type=int,   default=4,      help="troubled 振れ幅 px（デフォルト: 4）")
    p.add_argument("--troubled-frequency",  type=float, default=2.0,    help="troubled 周波数 Hz（デフォルト: 2.0）")
    p.add_argument("--chibi-amplitude",     type=int,   default=5,      help="chibi 振れ幅 px（デフォルト: 5）")
    p.add_argument("--chibi-frequency",     type=float, default=3.0,    help="chibi 周波数 Hz（デフォルト: 3.0）")
    # thinking
    p.add_argument("--zoom-duration",       type=float, default=2.0,    help="thinking zoom 完了までの秒数（デフォルト: 2.0）")
    p.add_argument("--zoom-max-scale",      type=float, default=1.1,    help="thinking 最大拡大率（デフォルト: 1.1）")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="感情アクション拡張デモ（9種）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_frames = sub.add_parser("frames", help="各感情の代表フレーム（PNG）を出力")
    _add_common_args(p_frames)

    p_video = sub.add_parser("video", help="各感情の動画（MP4）を出力")
    _add_common_args(p_video)
    p_video.add_argument("--duration", type=float, default=3.0, help="動画の長さ（秒、デフォルト: 3.0）")
    p_video.add_argument("--fps",      type=int,   default=30,  help="フレームレート（デフォルト: 30）")

    args = parser.parse_args()
    kwargs = _build_kwargs(args)

    if args.command == "frames":
        print("各感情の代表フレームを生成中...")
        generate_frames(args.image, output_dir=args.out, kwargs=kwargs)
    elif args.command == "video":
        print("各感情の動画を生成中...")
        generate_video(args.image, output_dir=args.out, duration_sec=args.duration, fps=args.fps, kwargs=kwargs)


if __name__ == "__main__":
    main()
