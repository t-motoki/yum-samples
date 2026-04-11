"""
ep3.4.1 サンプル: SadTalker CPU デモ

静止画像 + 音声ファイルから、顔が動くアニメーション動画を生成する。
GPU なし（CPU のみ）で動作する。

必要なもの:
  git clone https://github.com/OpenTalker/SadTalker.git
  cd SadTalker && pip install -r requirements.txt
  モデルのダウンロード（README 参照）

使い方:
  python sadtalker_demo.py --image face.png --audio voice.wav

注意:
  CPU 処理は非常に遅い。3〜4 秒の動画生成に 10〜15 分かかる。
  短い音声（3〜5 秒）から試すことを強く推奨する。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


# SadTalker リポジトリのパス（このスクリプトと同じディレクトリに clone することを想定）
SADTALKER_DIR = Path(__file__).parent / "SadTalker"


def run_sadtalker(
    image: Path,
    audio: Path,
    output_dir: Path = Path("results"),
    sadtalker_dir: Path = SADTALKER_DIR,
    still: bool = True,
    preprocess: str = "crop",
    size: int = 256,
) -> int:
    """SadTalker inference.py を呼び出して顔アニメーション動画を生成する。

    Args:
        image:         入力顔画像（PNG / JPG）のパス
        audio:         入力音声ファイル（WAV）のパス
        output_dir:    出力ディレクトリ（タイムスタンプ付きサブフォルダが作られる）
        sadtalker_dir: SadTalker リポジトリのパス
        still:         True = 頭の動きを最小限に抑える（アニメキャラ向け）
        preprocess:    画像の前処理方法（"crop" が推奨）
        size:          出力解像度（256 or 512）
    Returns:
        inference.py の終了コード（0=成功）
    """
    if not sadtalker_dir.exists():
        print(f"エラー: SadTalker リポジトリが見つかりません: {sadtalker_dir}")
        print("  git clone https://github.com/OpenTalker/SadTalker.git")
        return 1

    inference_py = sadtalker_dir / "inference.py"
    if not inference_py.exists():
        print(f"エラー: inference.py が見つかりません: {inference_py}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(inference_py),
        "--source_image", str(image.resolve()),
        "--driven_audio", str(audio.resolve()),
        "--result_dir",   str(output_dir.resolve()),
        "--checkpoint_dir", str((sadtalker_dir / "checkpoints").resolve()),
        "--preprocess",   preprocess,
        "--size",         str(size),
        "--cpu",  # GPU なしで動作させる
    ]

    if still:
        cmd.append("--still")  # 頭の揺れを抑える

    print(f"[image]  {image}")
    print(f"[audio]  {audio}")
    print(f"[output] {output_dir}")
    print(f"[still]  {still}")
    print()
    print("処理を開始します（CPU モードは数分〜十数分かかります）...")
    print()

    start = time.time()
    result = subprocess.run(cmd, cwd=str(sadtalker_dir))
    elapsed = time.time() - start

    if result.returncode == 0:
        m, s = divmod(int(elapsed), 60)
        print(f"\n完了（{m}分{s}秒）: {output_dir} 以下にタイムスタンプフォルダが作成されます")
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SadTalker CPU デモ — 静止画像 + 音声 → 顔アニメーション動画",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--image",  type=Path, required=True, help="入力顔画像（PNG / JPG）")
    parser.add_argument("--audio",  type=Path, required=True, help="入力音声ファイル（WAV）")
    parser.add_argument("--output", type=Path, default=Path("results"), help="出力ディレクトリ（デフォルト: results）")
    parser.add_argument("--sadtalker-dir", type=Path, default=SADTALKER_DIR, help="SadTalker リポジトリのパス")
    parser.add_argument("--no-still", action="store_true", help="頭の揺れを有効にする（デフォルトは still モード）")
    parser.add_argument("--size", type=int, default=256, choices=[256, 512], help="出力解像度（デフォルト: 256）")
    parser.add_argument(
        "--preprocess",
        default="crop",
        choices=["crop", "resize", "full"],
        help="前処理方法（デフォルト: crop）",
    )
    args = parser.parse_args()

    rc = run_sadtalker(
        image=args.image,
        audio=args.audio,
        output_dir=args.output,
        sadtalker_dir=args.sadtalker_dir,
        still=not args.no_still,
        preprocess=args.preprocess,
        size=args.size,
    )

    if rc != 0:
        print(f"\n失敗（終了コード: {rc}）", file=sys.stderr)
        sys.exit(rc)


if __name__ == "__main__":
    main()
