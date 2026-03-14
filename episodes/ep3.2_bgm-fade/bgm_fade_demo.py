"""
ep3.2 サンプル: BGM フェードイン・フェードアウト デモ

動画の冒頭・末尾で BGM をフワッとフェードさせる実装のコアロジックをデモする。

必要なもの:
  pip install moviepy

使い方:
  # サンプル BGM（silence）で動作確認
  python bgm_fade_demo.py

  # 自前の BGM を使う場合
  python bgm_fade_demo.py --bgm your_bgm.mp3 --fade 2.0 --duration 10
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

try:
    from moviepy import AudioFileClip, AudioClip
    from moviepy import audio_effects as afx
except ImportError:
    print("moviepy が必要です: pip install moviepy")
    sys.exit(1)


def apply_bgm_fade(bgm_path: Path, total_duration: float, fade_sec: float, output_path: Path) -> None:
    """BGM をループしてフェードイン・フェードアウトを適用し、WAV に書き出す。

    Args:
        bgm_path:       BGM ファイルのパス（MP3 / WAV / OGG など）
        total_duration: 動画全体の秒数（BGM をこの長さにループ）
        fade_sec:       フェードイン・アウトの秒数（両端に同じ秒数を適用）
        output_path:    出力先 WAV パス
    """
    print(f"BGM 読み込み: {bgm_path}")
    bgm_raw = AudioFileClip(str(bgm_path))

    # ① BGM を動画尺にループ
    bgm_looped = afx.AudioLoop(duration=total_duration).apply(bgm_raw)
    print(f"  ループ後の長さ: {bgm_looped.duration:.1f}秒（元: {bgm_raw.duration:.1f}秒）")

    # ② 音量を下げる（ナレーションに被らないよう -70% 程度）
    bgm_quiet = afx.MultiplyVolume(0.3).apply(bgm_looped)

    # ③ フェードイン・フェードアウト適用
    if fade_sec > 0:
        bgm_quiet = afx.AudioFadeIn(fade_sec).apply(bgm_quiet)
        bgm_quiet = afx.AudioFadeOut(fade_sec).apply(bgm_quiet)
        print(f"  フェード適用: 冒頭 {fade_sec}秒 / 末尾 {fade_sec}秒")
    else:
        print("  フェードなし（fade_sec=0）")

    # ④ 書き出し
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bgm_quiet.write_audiofile(str(output_path), logger=None)
    print(f"出力完了: {output_path}")


def make_silent_bgm(duration: float) -> Path:
    """BGM ファイルがない場合のフォールバック: 無音 WAV を生成して返す。"""
    import numpy as np
    from moviepy import AudioClip

    print("BGM ファイルが指定されていないため、無音ファイルで動作確認します")
    silent = AudioClip(lambda t: [0, 0], duration=duration, fps=44100)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    silent.write_audiofile(tmp.name, logger=None)
    return Path(tmp.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="BGM フェードイン・フェードアウト デモ")
    parser.add_argument("--bgm",      type=Path,  default=None,  help="BGM ファイルパス（省略時は無音で動作確認）")
    parser.add_argument("--fade",     type=float, default=2.0,   help="フェード秒数（デフォルト: 2.0）")
    parser.add_argument("--duration", type=float, default=15.0,  help="動画想定秒数（デフォルト: 15.0）")
    parser.add_argument("--output",   type=Path,  default=Path("output/bgm_faded.wav"), help="出力先")
    args = parser.parse_args()

    bgm_path = args.bgm if args.bgm else make_silent_bgm(args.duration)

    apply_bgm_fade(
        bgm_path=bgm_path,
        total_duration=args.duration,
        fade_sec=args.fade,
        output_path=args.output,
    )

    print("\n--- フェードの仕組み ---")
    print(f"  冒頭 {args.fade}秒: 無音 → 通常音量（フェードイン）")
    print(f"  中間 {args.duration - args.fade * 2:.1f}秒: 通常音量")
    print(f"  末尾 {args.fade}秒: 通常音量 → 無音（フェードアウト）")


if __name__ == "__main__":
    main()
