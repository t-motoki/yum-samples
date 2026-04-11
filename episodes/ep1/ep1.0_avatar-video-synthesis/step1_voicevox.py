"""
Step 1: VOICEVOXで音声を生成する

前提: VOICEVOXが起動していること
  docker compose up -d voicevox

使い方:
  python step1_voicevox.py "こんにちは、ゆむです。"
  → output.wav が生成される
"""

import sys
from pathlib import Path

import requests

VOICEVOX_URL = "http://localhost:50021"
SPEAKER_ID = 56  # 猫使アル おちつき


def generate_voice(text: str, output_path: str = "output.wav") -> None:
    # Step 1: 音声パラメータを取得
    query = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": SPEAKER_ID},
    ).json()

    # Step 2: 音声を合成
    wav = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": SPEAKER_ID},
        json=query,
    ).content

    Path(output_path).write_bytes(wav)
    print(f"完了: {output_path}")


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "こんにちは、ゆむです。"
    generate_voice(text)
