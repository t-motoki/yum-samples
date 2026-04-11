"""
ep3.7 サンプル: char_flip per-scene / pip start=N

dialogue レイアウトでのキャラクター向き制御と、
pip の再生開始位置を指定する仕組みのデモ。

台本での書き方:
  <!-- char_flip: true,true -->   # 両キャラを右向き（PiP を一緒に見る構図）
  <!-- char_flip: true,false -->  # ゆむ右向き・さばきゃん左向き（向き合い）
  <!-- char_flip: reset -->       # シーン単位設定を解除してデフォルトに戻す

  <!-- pip: video.mp4 position=right size=42% loop=false start=100 -->
  # start=100: 動画の100秒目から再生する

必要なもの:
  追加インストール不要（標準ライブラリのみ）

使い方:
  python char_flip_pip_start_demo.py              # 全デモを実行する
  python char_flip_pip_start_demo.py char_flip    # char_flip のパース結果を確認する
  python char_flip_pip_start_demo.py pip_start    # pip start=N の ffmpeg コマンドを確認する
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ──────────────────────────────────────────────
# ドメイン
# ──────────────────────────────────────────────

@dataclass
class CharFlipOverride:
    """シーン単位の char_flip 設定。

    dialogue_order の順番に対応する bool リスト。
    True = 左右反転する（右向き）、False = 反転しない（左向き）。
    """
    values: list[bool]  # [yumu_flip, sabacyan_flip] など dialogue_order と同順

    @classmethod
    def parse(cls, raw: str) -> "CharFlipOverride | None":
        """<!-- char_flip: true,false --> 形式の文字列をパースする。

        'reset' の場合は None を返す（シーン設定を解除してデフォルトに戻す）。

        Args:
            raw: ディレクティブの値部分（例: "true,false" / "true,true" / "reset"）

        Returns:
            CharFlipOverride。"reset" の場合は None。

        Examples:
            >>> CharFlipOverride.parse("true,false").values
            [True, False]
            >>> CharFlipOverride.parse("true,true").values
            [True, True]
            >>> CharFlipOverride.parse("reset") is None
            True
        """
        stripped = raw.strip().lower()
        if stripped == "reset":
            return None  # シーン単位設定を解除

        parts = [p.strip() for p in stripped.split(",")]
        values: list[bool] = []
        for part in parts:
            if part == "true":
                values.append(True)
            elif part == "false":
                values.append(False)
            else:
                print(
                    f"警告: char_flip の値 '{part}' は 'true'/'false' のいずれかである必要があります。"
                    f"'false' にフォールバックします。",
                    file=sys.stderr,
                )
                values.append(False)

        return cls(values=values)

    def should_flip(self, char_index: int) -> bool:
        """指定インデックスのキャラクターを反転すべきか返す。

        インデックスが範囲外の場合は False を返す。

        Args:
            char_index: dialogue_order 内のインデックス（0 始まり）

        Returns:
            True なら左右反転する
        """
        if char_index < len(self.values):
            return self.values[char_index]
        return False


@dataclass
class PipConfig:
    """PiP オーバーレイの設定。ep3.7 で start_sec パラメータを追加。"""
    path: Path
    position: str = "bottom-right"
    size_percent: int = 30
    loop: bool = True
    pip_audio: bool = False
    start_sec: float = 0.0  # ep3.7 追加: 再生開始位置（秒）


# ──────────────────────────────────────────────
# パーサー
# ──────────────────────────────────────────────

def parse_char_flip_directives(
    script_text: str,
    dialogue_order: list[str],
) -> list[tuple[int, str, CharFlipOverride | None]]:
    """台本テキストから char_flip ディレクティブを抽出する。

    Args:
        script_text: 台本の全テキスト
        dialogue_order: キャラクターの並び順（例: ["yumu", "sabacyan"]）

    Returns:
        (行番号, 元テキスト, CharFlipOverride | None) のリスト。
        None は <!-- char_flip: reset --> に対応する。
    """
    results = []
    for lineno, line in enumerate(script_text.splitlines(), start=1):
        stripped = line.strip()
        m = re.match(r"<!--\s*char_flip:\s*(.+?)\s*-->$", stripped)
        if not m:
            continue
        override = CharFlipOverride.parse(m.group(1))
        results.append((lineno, stripped, override))
    return results


def parse_pip_start(directive_text: str) -> tuple[Path | None, float]:
    """pip ディレクティブから path と start_sec を抽出する。

    Args:
        directive_text: ディレクティブ全体（例: "<!-- pip: video.mp4 start=100 loop=false -->"）

    Returns:
        (path, start_sec) のタプル。pip: stop の場合は (None, 0.0)。
    """
    m = re.match(r"<!--\s*pip:\s*(.+?)\s*-->$", directive_text.strip())
    if not m:
        return None, 0.0

    raw = m.group(1).strip()
    if raw == "stop":
        return None, 0.0

    tokens = raw.split()
    path = Path(tokens[0])
    start_sec = 0.0

    for token in tokens[1:]:
        if "=" not in token:
            continue
        key, _, value = token.partition("=")
        if key == "start":
            try:
                parsed = float(value)
                if parsed >= 0:
                    start_sec = parsed
                else:
                    print(
                        f"警告: pip start='{value}' は 0 以上である必要があります。"
                        f"0 にフォールバックします。",
                        file=sys.stderr,
                    )
            except ValueError:
                print(
                    f"警告: pip start='{value}' は数値として解釈できません。"
                    f"0 にフォールバックします。",
                    file=sys.stderr,
                )

    return path, start_sec


# ──────────────────────────────────────────────
# レンダラー: char_flip の向き決定ロジック
# ──────────────────────────────────────────────

@dataclass
class VideoConfig:
    """動画設定（デモ用の簡略モデル）。"""
    dialogue_order: list[str]
    char_flip: list[bool] = field(default_factory=lambda: [False, False])
    dialogue_flip_right: bool = True  # デフォルト: 左キャラを反転して向き合い演出


def decide_flip(
    char_name: str,
    video: VideoConfig,
    char_flip_override: CharFlipOverride | None,
) -> bool:
    """キャラクターを反転すべきか決定する。

    優先順位:
      1. char_flip_override が設定されていれば優先する
      2. video.char_flip が [False, False] 以外なら使う
      3. フォールバック: dialogue_flip_right に基づく既存ロジック

    Args:
        char_name: キャラクター名
        video: 動画設定
        char_flip_override: シーン単位の上書き設定（None = 上書きなし）

    Returns:
        True なら左右反転する
    """
    # シーン単位の override を優先する
    effective = char_flip_override if char_flip_override is not None else (
        CharFlipOverride(values=video.char_flip)
        if any(video.char_flip)
        else None
    )

    if effective is not None:
        try:
            idx = video.dialogue_order.index(char_name)
            return effective.should_flip(idx)
        except ValueError:
            pass

    # フォールバック: 左キャラのみ反転（向き合い演出）
    if video.dialogue_flip_right and video.dialogue_order:
        left_name = video.dialogue_order[0]
        return char_name == left_name

    return False


# ──────────────────────────────────────────────
# ffmpeg コマンド: pip start=N の実装
# ──────────────────────────────────────────────

def build_ffmpeg_pip_with_start(
    main_video: Path,
    pip_video: Path,
    output: Path,
    start_sec: float,
    loop: bool,
    position_x: str = "W-w-20",
    position_y: str = "(H-h)/2",
    size_w: int = 800,
) -> list[str]:
    """pip start=N を含む ffmpeg コマンドを組み立てる（実行はしない）。

    loop=True と loop=False で戦略が異なる:

    loop=True:
        -ss N を -i の直前に置く（input seek）。
        -stream_loop -1 と組み合わせて開始位置からループ再生する。
        → ffmpeg がデコード前にシークするため高速。

    loop=False:
        filter_complex の trim フィルターで開始位置を指定する。
        setpts=PTS-STARTPTS でタイムスタンプをリセットする。
        → 正確なフレーム位置でのトリミングが可能。

    Args:
        main_video: 本編動画
        pip_video: PiP 動画
        output: 出力先
        start_sec: 再生開始位置（秒）
        loop: True ならループ再生する
        position_x: ffmpeg overlay の x 座標式
        position_y: ffmpeg overlay の y 座標式
        size_w: PiP 幅（px）

    Returns:
        ffmpeg コマンドを表す文字列リスト
    """
    cmd = ["ffmpeg", "-y"]
    cmd += ["-i", str(main_video)]

    if loop:
        # loop=true: -ss N は -i の直前に置く（input seek オプション）
        if start_sec > 0:
            cmd += ["-ss", f"{start_sec:.6g}"]
        cmd += ["-stream_loop", "-1", "-i", str(pip_video)]

        scale_filter = f"[1:v]scale={size_w}:-2[pip_scaled]"
        overlay_filter = f"[0:v][pip_scaled]overlay=x={position_x}:y={position_y}[vout]"
        filter_complex = f"{scale_filter}; {overlay_filter}"

    else:
        # loop=false: filter_complex の trim で開始位置を指定する
        cmd += ["-i", str(pip_video)]

        if start_sec > 0:
            # trim=start=N でトリミング、setpts でタイムスタンプをリセット
            scale_filter = (
                f"[1:v]trim=start={start_sec:.6g},setpts=PTS-STARTPTS,"
                f"scale={size_w}:-2:force_original_aspect_ratio=decrease[pip_scaled]"
            )
        else:
            scale_filter = (
                f"[1:v]scale={size_w}:-2:force_original_aspect_ratio=decrease[pip_scaled]"
            )

        # loop=false では tpad で末尾フレームを複製して PiP が消えないようにする
        scale_filter = scale_filter.replace("[pip_scaled]", ",tpad=stop=-1:stop_mode=clone[pip_scaled]")
        overlay_filter = f"[0:v][pip_scaled]overlay=x={position_x}:y={position_y}[vout]"
        filter_complex = f"{scale_filter}; {overlay_filter}"

    cmd += ["-filter_complex", filter_complex]
    cmd += ["-map", "[vout]", "-map", "0:a"]
    cmd += ["-c:a", "copy", "-c:v", "libx264", "-preset", "fast", str(output)]
    return cmd


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

SAMPLE_SCRIPT = """\
## S01: 通常会話

<!-- config: layout=dialogue -->
<!-- config: dialogue_order=yumu,sabacyan -->
<!-- config: dialogue_avatar_area=left -->
<!-- speaker: yumu -->
<!-- expression: normal -->
通常の会話シーン。ゆむが右向き・さばきゃんが左向きで向き合っています。

<!-- speaker: sabacyan -->
<!-- expression: normal -->
向き合いのデフォルト状態ですね。

---

## S02: PiP 鑑賞（両方が右の動画を向く）

<!-- char_flip: true,true -->
<!-- pip: output/episodes/ep3.0/video.mp4 position=right size=42% loop=false start=100 pip_audio=false -->
<!-- speaker: yumu -->
<!-- expression: normal -->
ふたりとも右の PiP 動画を向いています。start=100 で100秒目から再生します。

---

## S03: 別のエピソードに切り替え

<!-- char_flip: true,true -->
<!-- pip: output/episodes/ep3.4.2/video.mp4 position=right size=42% loop=false start=125 pip_audio=false -->
<!-- speaker: yumu -->
<!-- expression: normal -->
pip ディレクティブを書き直すと別の動画に切り替わります。start=125 で125秒目から。

---

## S04: 会話に戻る

<!-- pip: stop -->
<!-- char_flip: true,false -->
<!-- speaker: sabacyan -->
<!-- expression: normal -->
pip が止まり、向き合いに戻りました。

<!-- speaker: yumu -->
<!-- expression: normal -->
ふたりともデフォルトの向きです。
"""


def cmd_char_flip(dialogue_order: list[str]) -> None:
    """char_flip ディレクティブのパース結果と向き決定ロジックを表示する。"""
    print("─── 台本サンプル ───")
    print(SAMPLE_SCRIPT)

    print("─── char_flip ディレクティブの抽出結果 ───")
    results = parse_char_flip_directives(SAMPLE_SCRIPT, dialogue_order)
    for lineno, text, override in results:
        if override is None:
            print(f"  行{lineno:3d}: {text}  → reset（デフォルトに戻す）")
        else:
            flip_info = ", ".join(
                f"{dialogue_order[i]}={'反転' if v else '維持'}"
                for i, v in enumerate(override.values)
            )
            print(f"  行{lineno:3d}: {text}  → [{flip_info}]")

    print()
    print("─── 向き決定ロジックの確認 ───")
    video = VideoConfig(
        dialogue_order=dialogue_order,
        char_flip=[False, False],
        dialogue_flip_right=True,
    )

    scenarios = [
        ("通常会話（override なし）",   None),
        ("PiP 鑑賞（true,true）",       CharFlipOverride([True, True])),
        ("向き合いに戻す（true,false）", CharFlipOverride([True, False])),
    ]

    for label, override in scenarios:
        print(f"\n  [{label}]")
        for char in dialogue_order:
            flip = decide_flip(char, video, override)
            direction = "右向き（反転）" if flip else "左向き（維持）"
            print(f"    {char}: {direction}")


def cmd_pip_start() -> None:
    """pip start=N の ffmpeg コマンドを表示する。"""
    test_cases = [
        ("loop=true,  start=0",   True,  0.0),
        ("loop=true,  start=100", True,  100.0),
        ("loop=false, start=0",   False, 0.0),
        ("loop=false, start=125", False, 125.0),
    ]

    print("─── pip start=N の ffmpeg コマンド比較 ───")
    print()
    print("  loop=True  → -ss N を -i の直前に置く（input seek）")
    print("  loop=False → filter_complex の trim=start=N で開始位置を指定")
    print()

    for label, loop, start in test_cases:
        print(f"  【{label}】")
        cmd = build_ffmpeg_pip_with_start(
            main_video=Path("output/video_base.mp4"),
            pip_video=Path("output/episodes/ep3.0/video.mp4"),
            output=Path("output/video_pip.mp4"),
            start_sec=start,
            loop=loop,
        )
        # 見やすく折り返す
        print("    ffmpeg", end="")
        for i, token in enumerate(cmd[1:], start=1):
            if token.startswith("-") and not token.replace("-", "").replace(".", "").isdigit():
                print(f" \\\n      {token}", end="")
            else:
                print(f" '{token}'", end="")
        print()
        print()

    print("─── pip ディレクティブのパース（start パラメータ含む） ───")
    directives = [
        "<!-- pip: output/episodes/ep3.0/video.mp4 position=right size=42% loop=false start=100 pip_audio=false -->",
        "<!-- pip: output/episodes/ep3.4.2/video.mp4 position=right size=42% loop=true start=125 -->",
        "<!-- pip: output/episodes/ep3.6/video.mp4 position=right size=42% loop=false -->",
        "<!-- pip: stop -->",
    ]
    for d in directives:
        path, start_sec = parse_pip_start(d)
        if path is None:
            print(f"  {d}")
            print(f"    → PiP 終了")
        else:
            print(f"  {d}")
            print(f"    → path={path}  start={start_sec}s")
        print()


def main() -> None:
    dialogue_order = ["yumu", "sabacyan"]

    parser = argparse.ArgumentParser(description="char_flip / pip start=N デモ")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("char_flip", help="char_flip のパース結果と向き決定ロジックを確認する")
    sub.add_parser("pip_start", help="pip start=N の ffmpeg コマンドを確認する")
    args = parser.parse_args()

    if args.command == "char_flip":
        cmd_char_flip(dialogue_order)
    elif args.command == "pip_start":
        cmd_pip_start()
    else:
        print("=" * 60)
        print("char_flip per-scene / pip start=N デモ（全実行）")
        print("=" * 60)
        print()
        print("【1. char_flip】")
        cmd_char_flip(dialogue_order)
        print()
        print("【2. pip start=N】")
        cmd_pip_start()


if __name__ == "__main__":
    main()
