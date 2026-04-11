"""
ep3.3 サンプル: Wav2Lip リップシンク デモ

アニメキャラ画像 + 音声ファイルから口パク動画を生成する。
Wav2Lip の inference.py を Python から呼び出すラッパーのデモ。

必要なもの:
  git clone https://github.com/Rudrabha/Wav2Lip.git
  pip install torch torchvision librosa numpy opencv-python

使い方:
  # 基本（顔検出を自動で試みる）
  python wav2lip_demo.py --face avatar.png --audio voice.wav --output out.mp4

  # アニメキャラ向け（口座標を手動指定）
  python wav2lip_demo.py --face avatar.png --audio voice.wav --output out.mp4 \\
      --box 345 465 380 620

アニメキャラへの適用メモ:
  - Wav2Lip は実写顔（LRS2 データセット）で学習 → アニメ顔では検出が不安定
  - S3FD（顔検出器）が顔を誤認識し、口以外の座標を返すことがある
  - --box y1 y2 x1 x2 で口〜顎エリアを直接指定すると安定する
  - box の下半分に口〜顎が収まるよう調整するのがコツ
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


# Wav2Lip リポジトリのパス（このスクリプトからの相対パスで探す）
# git clone https://github.com/Rudrabha/Wav2Lip.git した場所に合わせて変更する
WAV2LIP_DIR = Path(__file__).parent / "Wav2Lip"

DEFAULT_CHECKPOINT = WAV2LIP_DIR / "checkpoints" / "Wav2Lip-SD-NOGAN.pt"


def run_wav2lip(
    face: Path,
    audio: Path,
    output: Path,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    box: list[int] | None = None,
    static: bool = True,
    resize_factor: int = 1,
) -> int:
    """Wav2Lip inference.py を呼び出してリップシンク動画を生成する。

    Args:
        face:          顔画像（PNG / JPG）または動画（MP4）のパス
        audio:         音声ファイルのパス（WAV）
        output:        出力動画のパス（MP4）
        checkpoint:    Wav2Lip モデルのチェックポイントパス
        box:           顔バウンディングボックス [y1, y2, x1, x2]（None で自動検出）
        static:        True = 静止画として処理（毎フレーム顔検出をスキップして高速化）
        resize_factor: 解像度縮小係数（1=原寸, 2=半分）
    Returns:
        inference.py の終了コード（0=成功）
    """
    if not WAV2LIP_DIR.exists():
        print(f"エラー: Wav2Lip リポジトリが見つかりません: {WAV2LIP_DIR}")
        print("  git clone https://github.com/Rudrabha/Wav2Lip.git")
        return 1

    if not checkpoint.exists():
        print(f"エラー: モデルが見つかりません: {checkpoint}")
        print("  https://github.com/Rudrabha/Wav2Lip からモデルをダウンロードしてください")
        return 1

    # subprocess は Wav2Lip ディレクトリ内で実行するため、パスを絶対パスに変換
    face_abs = str(face.resolve())
    audio_abs = str(audio.resolve())
    output_abs = str(output.resolve())

    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(WAV2LIP_DIR / "inference.py"),
        "--checkpoint_path", str(checkpoint.resolve()),
        "--face",            face_abs,
        "--audio",           audio_abs,
        "--outfile",         output_abs,
        "--resize_factor",   str(resize_factor),
    ]

    if static:
        cmd += ["--static", "True"]  # 静止画モード: 顔検出を初回のみ実行

    if box is not None:
        cmd += ["--box"] + [str(v) for v in box]
        print(f"[box] y1={box[0]} y2={box[1]} x1={box[2]} x2={box[3]}  ← アニメ顔に合わせた手動指定")
    else:
        print("[box] 自動検出モード（アニメ顔では不安定な場合あり）")

    print(f"[face]   {face_abs}")
    print(f"[audio]  {audio_abs}")
    print(f"[output] {output_abs}")
    print()

    result = subprocess.run(cmd, cwd=str(WAV2LIP_DIR))
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wav2Lip リップシンク デモ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--face",    type=Path, required=True, help="顔画像（PNG/JPG）または動画（MP4）")
    parser.add_argument("--audio",   type=Path, required=True, help="音声ファイル（WAV）")
    parser.add_argument("--output",  type=Path, default=Path("output/lipsync.mp4"), help="出力動画（デフォルト: output/lipsync.mp4）")
    parser.add_argument(
        "--box",
        nargs=4, type=int, metavar=("Y1", "Y2", "X1", "X2"),
        default=None,
        help="顔バウンディングボックス（y1 y2 x1 x2）。アニメ顔では必須に近い",
    )
    parser.add_argument("--checkpoint",    type=Path, default=DEFAULT_CHECKPOINT, help="モデルチェックポイントのパス")
    parser.add_argument("--no-static",     action="store_true", help="動画モード（デフォルトは静止画モード）")
    parser.add_argument("--resize-factor", type=int, default=1, help="解像度縮小係数（1=原寸, 2=半分）")
    args = parser.parse_args()

    rc = run_wav2lip(
        face=args.face,
        audio=args.audio,
        output=args.output,
        checkpoint=args.checkpoint,
        box=args.box,
        static=not args.no_static,
        resize_factor=args.resize_factor,
    )

    if rc == 0:
        print(f"\n完了: {args.output}")
    else:
        print(f"\n失敗（終了コード: {rc}）", file=sys.stderr)
        sys.exit(rc)


if __name__ == "__main__":
    main()
