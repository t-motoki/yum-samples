"""
ep3.5.5 サンプル: SE（効果音）ディレクティブ

台本に1行書くだけで効果音を鳴らせる仕組みのデモ。

台本での書き方:
  <!-- se: ひらめく1 -->           # シーン先頭で鳴らす
  <!-- se: スイッチを押す offset=1.5 -->   # シーン開始から1.5秒後に鳴らす

仕組みの概要:
  1. パーサーが <!-- se: プリセット名 --> を読んで SECue オブジェクトに変換する
  2. SEPresetResolver がプリセット名 → 音声ファイルパスに変換する
  3. ナレーション音声と SE 音声を CompositeAudioClip でミックスする
  4. BGM とは独立して動くため、BGM 音量を変えても SE タイミングは変わらない

必要なもの:
  pip install moviepy

使い方:
  # SE ファイルを指定してミックス結果を確認する
  python se_demo.py mix --narration narration.wav --se se_sound.mp3

  # offset 付きでミックスする（ナレーション開始から1.5秒後に SE を鳴らす）
  python se_demo.py mix --narration narration.wav --se se_sound.mp3 --offset 1.5

  # 複数の SE をミックスする
  python se_demo.py mix --narration narration.wav --se se1.mp3 --se se2.mp3 --offset 0 2.0

  # パーサーの動作だけを確認する（音声ファイル不要）
  python se_demo.py parse
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ──────────────────────────────────────────────
# ドメイン: SECue（効果音の再生タイミングを保持する値オブジェクト）
# ──────────────────────────────────────────────

@dataclass
class SECue:
    """効果音の再生タイミング。

    Attributes:
        preset: プリセット名（SE ファイルの拡張子を除いたファイル名）
        offset: シーン開始からの秒数（0.0 = シーン先頭）
    """
    preset: str
    offset: float = 0.0

    def __post_init__(self):
        if self.offset < 0.0:
            raise ValueError(f"offset は 0.0 以上である必要があります: {self.offset}")


# ──────────────────────────────────────────────
# インフラ: SEPresetResolver（プリセット名 → ファイルパス）
# ──────────────────────────────────────────────

class SEPresetResolver:
    """プリセット名から音声ファイルパスを解決する。

    デフォルトは src/assets/se/ を探索するが、
    asset_dir を差し替えることで任意のディレクトリを使える。
    """

    def __init__(self, asset_dir: Path = Path("src/assets/se")) -> None:
        self._asset_dir = asset_dir

    def resolve(self, preset: str) -> Path | None:
        """プリセット名 → Path 変換。.wav → .mp3 → .ogg の順で探す。"""
        for ext in (".wav", ".mp3", ".ogg"):
            candidate = self._asset_dir / f"{preset}{ext}"
            if candidate.exists():
                return candidate
        print(
            f"警告: SE プリセット '{preset}' が見つかりません "
            f"（{self._asset_dir}/{preset}.[wav|mp3|ogg] を確認してください）",
            file=sys.stderr,
        )
        return None

    def list_presets(self) -> list[str]:
        """利用可能なプリセット名の一覧を返す。"""
        presets = []
        for ext in (".wav", ".mp3", ".ogg"):
            for p in sorted(self._asset_dir.glob(f"*{ext}")):
                presets.append(p.stem)
        return presets


# ──────────────────────────────────────────────
# パーサー: 台本テキストから SECue を抽出する
# ──────────────────────────────────────────────

def parse_se_directives(script_text: str) -> list[tuple[int, SECue]]:
    """台本テキストから SE ディレクティブを抽出する。

    Args:
        script_text: 台本の全テキスト

    Returns:
        (行番号, SECue) のリスト

    Examples:
        >>> cues = parse_se_directives("<!-- se: ひらめく1 -->")
        >>> cues[0][1].preset
        'ひらめく1'
        >>> cues[0][1].offset
        0.0

        >>> cues = parse_se_directives("<!-- se: スイッチを押す offset=1.5 -->")
        >>> cues[0][1].offset
        1.5
    """
    # <!-- se: プリセット名 --> または <!-- se: プリセット名 offset=N.N -->
    pattern = re.compile(
        r"<!--\s*se:\s*(.+?)(?:\s+offset=(\d+(?:\.\d+)?))?\s*-->",
        re.IGNORECASE,
    )
    results = []
    for lineno, line in enumerate(script_text.splitlines(), start=1):
        m = pattern.search(line)
        if m:
            preset = m.group(1).strip()
            offset = float(m.group(2)) if m.group(2) else 0.0
            results.append((lineno, SECue(preset=preset, offset=offset)))
    return results


# ──────────────────────────────────────────────
# ミキサー: ナレーション音声 + SE 音声を合成する
# ──────────────────────────────────────────────

def mix_narration_and_se(
    narration_path: Path,
    se_cues: list[SECue],
    resolver: SEPresetResolver,
    output_path: Path,
) -> None:
    """ナレーション音声と SE 音声を CompositeAudioClip でミックスして書き出す。

    設計のポイント:
    - SE は with_start(offset) で配置するだけで、ナレーションとは独立している
    - BGM は別の ffmpeg amix フローで処理するため、ここでは BGM を考慮しない
    - SE が複数ある場合は全部まとめて 1 つの CompositeAudioClip にミックスする

    Args:
        narration_path: ナレーション音声ファイル（WAV / MP3）
        se_cues: SECue のリスト
        resolver: プリセット名 → ファイルパス解決器
        output_path: 出力先（WAV / MP3）
    """
    from moviepy import AudioFileClip, CompositeAudioClip

    narration = AudioFileClip(str(narration_path))
    tracks = [narration]

    for cue in se_cues:
        path = resolver.resolve(cue.preset)
        if path is None:
            continue
        se_audio = AudioFileClip(str(path)).with_start(cue.offset)
        tracks.append(se_audio)
        print(f"  SE '{cue.preset}' を {cue.offset:.1f}s に配置")

    if len(tracks) == 1:
        print("SE なし: ナレーションのみ出力します")
        mixed = narration
    else:
        mixed = CompositeAudioClip(tracks)

    mixed.write_audiofile(str(output_path))
    print(f"出力: {output_path} ({mixed.duration:.2f}s)")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

SAMPLE_SCRIPT = """\
## scene1: はじめに

<!-- speaker: yumu -->
<!-- se: ひらめく1 -->
台本に1行書くだけで、効果音が鳴るようにしました。

## scene2: デモ

<!-- speaker: yumu -->
<!-- se: スイッチを押す offset=1.5 -->
「offset=1.5」と書くと、シーン開始から1.5秒後に鳴ります。

## scene3: 複数 SE

<!-- speaker: yumu -->
<!-- se: ひらめく1 -->
<!-- se: きらきら輝く3 offset=2.0 -->
複数の SE を同じシーンに入れることもできます。
"""


def cmd_parse(args: argparse.Namespace) -> None:
    """台本サンプルから SE ディレクティブを抽出して表示する。"""
    print("─── 台本サンプル ───")
    print(SAMPLE_SCRIPT)
    print("─── 抽出された SECue ───")
    cues = parse_se_directives(SAMPLE_SCRIPT)
    if not cues:
        print("SE ディレクティブが見つかりませんでした")
        return
    for lineno, cue in cues:
        print(f"  行{lineno:3d}: preset='{cue.preset}'  offset={cue.offset:.1f}s")


def cmd_list(args: argparse.Namespace) -> None:
    """利用可能なプリセット一覧を表示する。"""
    resolver = SEPresetResolver(Path(args.asset_dir))
    presets = resolver.list_presets()
    if not presets:
        print(f"プリセットが見つかりません: {args.asset_dir}")
        return
    print(f"利用可能なプリセット ({len(presets)}件):")
    for p in presets:
        print(f"  {p}")


def cmd_mix(args: argparse.Namespace) -> None:
    """ナレーション音声 + SE をミックスして出力する。"""
    narration = Path(args.narration)
    if not narration.exists():
        print(f"エラー: ナレーション音声が見つかりません: {narration}", file=sys.stderr)
        sys.exit(1)

    # --se と --offset を SECue に変換する
    offsets = args.offset or []
    se_paths = args.se or []
    # offset の数が SE の数より少ない場合は 0.0 で埋める
    while len(offsets) < len(se_paths):
        offsets.append(0.0)

    cues = [
        SECue(preset=Path(se).stem, offset=float(offsets[i]))
        for i, se in enumerate(se_paths)
    ]

    resolver = SEPresetResolver(Path(args.asset_dir))
    output = Path(args.output)

    print(f"ナレーション: {narration}")
    for cue in cues:
        print(f"  SE: '{cue.preset}'  offset={cue.offset:.1f}s")

    mix_narration_and_se(narration, cues, resolver, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="SE ディレクティブ デモ")
    parser.add_argument(
        "--asset-dir", default="src/assets/se",
        help="SE アセットディレクトリ（デフォルト: src/assets/se）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # parse: 台本サンプルから SECue を抽出
    sub.add_parser("parse", help="台本サンプルから SE ディレクティブを抽出して表示")

    # list: プリセット一覧
    sub.add_parser("list", help="利用可能な SE プリセット一覧を表示")

    # mix: ナレーション + SE をミックス
    p_mix = sub.add_parser("mix", help="ナレーション音声と SE をミックスして出力")
    p_mix.add_argument("--narration", required=True, help="ナレーション音声ファイル")
    p_mix.add_argument("--se", action="append", help="SE 音声ファイル（複数指定可）")
    p_mix.add_argument(
        "--offset", action="append", type=float,
        help="SE のオフセット秒数（--se と同じ順で指定）",
    )
    p_mix.add_argument("--output", default="mixed.wav", help="出力ファイル（デフォルト: mixed.wav）")

    args = parser.parse_args()
    {"parse": cmd_parse, "list": cmd_list, "mix": cmd_mix}[args.command](args)


if __name__ == "__main__":
    main()
