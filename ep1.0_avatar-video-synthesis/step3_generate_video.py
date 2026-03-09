"""
Step 3: MoviePyでフレーム画像と音声を合わせてMP4を生成する

前提:
  pip install moviepy
  frame.png と audio.wav を用意する（step1・step2で生成したもの）

使い方:
  python step3_generate_video.py frame.png audio.wav
  → output.mp4 が生成される
"""

import sys

from moviepy import AudioFileClip, ImageClip


def generate_video(frame_path: str, audio_path: str, output_path: str = "output.mp4") -> None:
    audio = AudioFileClip(audio_path)
    clip = ImageClip(frame_path).with_audio(audio).with_duration(audio.duration)
    clip.write_videofile(output_path, fps=30, codec="libx264")
    print(f"完了: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使い方: python step3_generate_video.py <frame.png> <audio.wav>")
        sys.exit(1)
    generate_video(sys.argv[1], sys.argv[2])
