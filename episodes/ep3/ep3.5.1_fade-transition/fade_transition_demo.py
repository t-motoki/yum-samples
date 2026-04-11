"""
フェードトランジション デモ

赤・緑・青のカラーブロック動画をクロスフェードで繋ぐデモ。
crossfade 時に音声がずれる問題の解決策を実装している。

使い方:
    python fade_transition_demo.py --duration 2 --tr-sec 0.5 --output output.mp4
"""

import argparse
import numpy as np
from moviepy import (
    ColorClip,
    AudioArrayClip,
    CompositeAudioClip,
    concatenate_videoclips,
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut


# ──────────────────────────────────────────────
# 音声生成
# ──────────────────────────────────────────────

def make_tone(frequency: float, duration: float, fps: int = 44100) -> AudioArrayClip:
    """サイン波トーンを AudioArrayClip として生成する。

    WAV ファイル不要でデモ用の音声を埋め込むために使う。
    """
    t = np.linspace(0, duration, int(fps * duration), endpoint=False)
    wave = 0.3 * np.sin(2 * np.pi * frequency * t)  # 音量は 0.3 に抑える
    # AudioArrayClip はステレオ（shape: [samples, 2]）を期待する
    stereo = np.stack([wave, wave], axis=1)
    return AudioArrayClip(stereo, fps=fps)


# ──────────────────────────────────────────────
# クリップ生成
# ──────────────────────────────────────────────

SCENES = [
    {"color": (220, 50, 50),  "tone_hz": 440.0, "label": "赤"},   # A4
    {"color": (50, 200, 80),  "tone_hz": 523.3, "label": "緑"},   # C5
    {"color": (50, 80, 220),  "tone_hz": 659.3, "label": "青"},   # E5
]


def make_clip(scene: dict, duration: float, tr_sec: float, size: tuple[int, int]):
    """1シーン分のクリップ（映像 + 音声）を生成する。

    crossfade のズレ対策として、クリップの duration を
    audio.duration + tr_sec に伸ばし、音声末尾に無音バッファを作る。
    こうすることで padding=-tr_sec で映像が重なっても
    音声は重ならない。
    """
    # 映像: 単色ブロック
    video = ColorClip(size=size, color=scene["color"], duration=duration + tr_sec)

    # 音声: サイン波トーン（元の duration 分のみ鳴らす）
    tone = make_tone(scene["tone_hz"], duration)

    # CompositeAudioClip でラップすると duration を明示的に伸ばせる。
    # ラップしないと set_duration() が音声を繰り返し再生してしまう。
    audio_with_buffer = CompositeAudioClip([tone]).with_duration(duration + tr_sec)

    clip = video.with_audio(audio_with_buffer)
    return clip


# ──────────────────────────────────────────────
# トランジション適用
# ──────────────────────────────────────────────

def apply_crossfade(clips: list, tr_sec: float) -> list:
    """各クリップにクロスフェードエフェクトを付与する。

    先頭クリップは CrossFadeOut のみ、末尾クリップは CrossFadeIn のみ、
    中間クリップは両方を付ける。
    """
    result = []
    for i, clip in enumerate(clips):
        is_first = i == 0
        is_last = i == len(clips) - 1

        if not is_first:
            clip = clip.with_effects([CrossFadeIn(tr_sec)])
        if not is_last:
            clip = clip.with_effects([CrossFadeOut(tr_sec)])

        result.append(clip)
    return result


# ──────────────────────────────────────────────
# メイン
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="クロスフェードトランジション デモ"
    )
    parser.add_argument(
        "--duration", type=float, default=2.0,
        help="各シーンの秒数（デフォルト: 2.0）"
    )
    parser.add_argument(
        "--tr-sec", type=float, default=0.5,
        help="クロスフェード秒数（デフォルト: 0.5）"
    )
    parser.add_argument(
        "--output", type=str, default="output.mp4",
        help="出力ファイルパス（デフォルト: output.mp4）"
    )
    args = parser.parse_args()

    size = (640, 360)

    print("クリップを生成しています...")
    clips = [
        make_clip(scene, args.duration, args.tr_sec, size)
        for scene in SCENES
    ]

    print("クロスフェードを適用しています...")
    clips = apply_crossfade(clips, args.tr_sec)

    # padding=-tr_sec で映像を tr_sec 分重ねる。
    # method="compose" を指定しないと crossfade が効かない。
    print("クリップを連結しています...")
    final = concatenate_videoclips(clips, method="compose", padding=-args.tr_sec)

    print(f"書き出し中: {args.output}")
    final.write_videofile(
        args.output,
        fps=30,
        audio_codec="aac",
        logger="bar",
    )
    print(f"完了: {args.output}")


if __name__ == "__main__":
    main()
