"""
ep3.4.2 サンプル: Rhubarb Lip Sync デモ

音声ファイル（WAV）から口の形（viseme）のタイミングデータを取得し、
アバターの表情に変換する最小実装。

Rhubarb は映像合成をしない。
「この時刻にこの口の形」というデータを出力するだけ。
映像への適用は自分の側で行う。

必要なもの:
  Rhubarb Lip Sync バイナリ（無料・OSS）
  https://github.com/DanielSWolf/rhubarb-lip-sync/releases

使い方:
  python rhubarb_demo.py --audio voice.wav
  python rhubarb_demo.py --audio voice.wav --rhubarb /path/to/rhubarb
  python rhubarb_demo.py --audio voice.wav --time 1.5
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


# ──────────────────────────────────────────────
# viseme → アバター表情名のマッピング
# ──────────────────────────────────────────────
# Rhubarb の viseme 体系（A〜H + X）をプロジェクトの表情絵に対応させる。
# 今回は3種類の絵に集約している:
#   normal       … 口を閉じた状態（無音・閉音）
#   lipsync_open … 大きく開いた状態（"あ行" 系の大開口）
#   lipsync_half … 中間・半開き（上記以外の有声音）
_VISEME_MAP: dict[str, str] = {
    "X": "normal",        # 無音・休止
    "A": "lipsync_open",  # 大開口（"aa" 音） → 口を大きく開いた絵
    "B": "normal",        # 閉音（"p", "b", "m"） → 唇を閉じた絵
    "C": "lipsync_half",  # 歯間音
    "D": "lipsync_half",  # 歯茎音
    "E": "lipsync_half",  # 前舌母音
    "F": "lipsync_half",  # 唇歯音
    "G": "lipsync_half",  # 舌後部音
    "H": "lipsync_half",  # 丸め音
}


def viseme_to_expression(viseme: str) -> str:
    """Rhubarb の viseme 値をアバター表情名に変換する。

    未知の値は "normal" にフォールバックする。
    """
    return _VISEME_MAP.get(viseme, "normal")


# ──────────────────────────────────────────────
# データクラス
# ──────────────────────────────────────────────

@dataclass
class VisemeCue:
    """Rhubarb が出力するひとつの口形素タイミング。"""
    start: float   # 開始時刻（秒）
    end: float     # 終了時刻（秒）
    value: str     # viseme 値（"A"〜"H" または "X"）

    @property
    def expression(self) -> str:
        """このタイミングに対応するアバター表情名。"""
        return viseme_to_expression(self.value)


# ──────────────────────────────────────────────
# Rhubarb 呼び出し
# ──────────────────────────────────────────────

def extract_visemes(wav_path: Path, rhubarb_bin: str = "rhubarb") -> list[VisemeCue]:
    """WAV ファイルを Rhubarb に通して VisemeCue リストを返す。

    Args:
        wav_path:    解析対象の WAV ファイル
        rhubarb_bin: Rhubarb バイナリのパスまたはコマンド名

    Returns:
        VisemeCue のリスト（時刻順）

    Raises:
        FileNotFoundError: wav_path が存在しない場合
        RuntimeError:      Rhubarb が非ゼロで終了した場合
    """
    if not wav_path.exists():
        raise FileNotFoundError(f"WAV ファイルが見つかりません: {wav_path}")

    result = subprocess.run(
        [rhubarb_bin, "-f", "json", str(wav_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Rhubarb の実行に失敗しました（終了コード: {result.returncode}）\n"
            f"{result.stderr}"
        )

    data = json.loads(result.stdout)
    return [
        VisemeCue(start=c["start"], end=c["end"], value=c["value"])
        for c in data["mouthCues"]
    ]


def find_expression_at(cues: list[VisemeCue], time_sec: float) -> str:
    """指定時刻に対応するアバター表情名を返す。

    Rhubarb の mouthCues は連続して隙間なく並んでいるが、
    念のため範囲外は "normal" にフォールバックする。

    Args:
        cues:     extract_visemes() が返したリスト
        time_sec: 問い合わせたい時刻（秒）

    Returns:
        アバター表情名（"normal" / "lipsync_open" / "lipsync_half"）
    """
    for cue in cues:
        if cue.start <= time_sec < cue.end:
            return cue.expression
    return "normal"


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rhubarb Lip Sync デモ — WAV から viseme タイミングを取得してアバター表情に変換する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--audio", type=Path, required=True, help="入力音声ファイル（WAV）")
    parser.add_argument(
        "--rhubarb",
        default="rhubarb",
        help="Rhubarb バイナリのパス（デフォルト: PATH 上の rhubarb）",
    )
    parser.add_argument(
        "--time",
        type=float,
        default=None,
        help="指定時刻（秒）での表情を問い合わせる（省略時は全タイムラインを表示）",
    )
    args = parser.parse_args()

    print(f"[audio]   {args.audio}")
    print(f"[rhubarb] {args.rhubarb}")
    print()

    try:
        cues = extract_visemes(args.audio, rhubarb_bin=args.rhubarb)
    except FileNotFoundError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"エラー: {e}", file=sys.stderr)
        print(
            "\nヒント: Rhubarb バイナリが見つからない場合は --rhubarb オプションでパスを指定してください",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.time is not None:
        # 指定時刻の表情を返す
        expr = find_expression_at(cues, args.time)
        print(f"時刻 {args.time:.3f}s → 表情: {expr}")
    else:
        # 全タイムラインを表示
        duration = cues[-1].end if cues else 0.0
        print(f"総時間: {duration:.3f}s  / {len(cues)} cues")
        print()
        print(f"{'start':>8}  {'end':>8}  {'viseme':>6}  expression")
        print("-" * 44)
        for cue in cues:
            print(
                f"{cue.start:8.3f}  {cue.end:8.3f}  {cue.value:>6}  {cue.expression}"
            )


if __name__ == "__main__":
    main()
