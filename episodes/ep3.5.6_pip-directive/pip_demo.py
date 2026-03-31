"""
ep3.5.6 サンプル: PiP（ピクチャー・イン・ピクチャー）ディレクティブ

台本に1行書くだけでスクリーン録画などの動画をアバターシーンの隅に重ねられる
仕組みのデモ。

台本での書き方:
  <!-- pip: screen.mp4 -->                            # 右下に30%サイズで表示
  <!-- pip: screen.mp4 position=bottom-right size=35% loop=true -->  # 全パラメータ指定
  <!-- pip: stop -->                                  # PiP を終了

仕組みの概要:
  1. パーサーが <!-- pip: --> を読んで PipConfig オブジェクトに変換する
  2. シーンをまたいで PipConfig が引き継がれる（<!-- pip: stop --> まで持続）
  3. _build_pip_segments がシーン列 → (PipConfig, start_sec, end_sec) のリストに変換する
  4. _ffmpeg_pip_overlay が ffmpeg overlay フィルターで動画全体に PiP を合成する

必要なもの:
  追加インストール不要（標準ライブラリのみ）

使い方:
  # 全デモを実行する
  python pip_demo.py

  # ディレクティブのパース結果を表示する
  python pip_demo.py parse

  # セグメント合成の概念を表示する
  python pip_demo.py segment
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ──────────────────────────────────────────────
# ドメイン: PipConfig（PiP オーバーレイの設定を保持する値オブジェクト）
# ──────────────────────────────────────────────

# 利用可能な position プリセット一覧（9種類）
VALID_PIP_POSITIONS: frozenset[str] = frozenset({
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
    "center",
    "center-top",
    "center-bottom",
    "left",
    "right",
})


@dataclass
class PipConfig:
    """PiP オーバーレイの設定を保持する値オブジェクト。

    Attributes:
        path: PiP として重ねる動画ファイルのパス
        position: 配置位置プリセット（VALID_PIP_POSITIONS のいずれか）
        size_percent: PiP ウィンドウ幅を本編動画幅に対する割合で指定（1〜99）
        loop: True のとき PiP 動画が本編より短い場合にループ再生する
        pip_audio: True のとき PiP 動画の音声を本編音声にミックスする
    """
    path: Path
    position: str = "bottom-right"
    size_percent: int = 30
    loop: bool = True
    pip_audio: bool = False

    def __post_init__(self) -> None:
        # 不正値は呼び出し前に正規化するため、ここに到達した場合は確実にエラー
        if self.position not in VALID_PIP_POSITIONS:
            raise ValueError(
                f"position は {VALID_PIP_POSITIONS} のいずれかである必要があります: "
                f"{self.position}"
            )
        if not (1 <= self.size_percent <= 99):
            raise ValueError(
                f"size_percent は 1〜99 の範囲である必要があります: {self.size_percent}"
            )


# ──────────────────────────────────────────────
# パーサー: 台本テキストから PipConfig を抽出する
# ──────────────────────────────────────────────

def _parse_pip_directive(raw: str) -> PipConfig:
    """台本の pip ディレクティブ本体（<!-- pip: の後ろ部分）をパースして PipConfig を返す。

    不正値は stderr 警告 + フォールバック（動画生成が止まらないようにする）。
    'stop' の場合は呼び出し前に弾くこと。

    Args:
        raw: パスとオプションを含む生テキスト（例: "screen.mp4 position=top-right size=35%"）

    Returns:
        PipConfig オブジェクト。不正値はデフォルト値にフォールバックする（None は返さない）。
    """
    tokens = raw.strip().split()
    path = Path(tokens[0])

    # キーワード引数をパースする
    position = "bottom-right"
    size_percent = 30
    loop = True
    pip_audio = False

    for token in tokens[1:]:
        if "=" not in token:
            continue
        key, _, value = token.partition("=")

        if key == "position":
            if value in VALID_PIP_POSITIONS:
                position = value
            else:
                print(
                    f"警告: pip position '{value}' は無効です。"
                    f"'bottom-right' にフォールバックします。",
                    file=sys.stderr,
                )

        elif key == "size":
            if value.endswith("%"):
                try:
                    parsed = int(value[:-1])
                    if 1 <= parsed <= 99:
                        size_percent = parsed
                    else:
                        print(
                            f"警告: pip size '{value}' は範囲外（1%〜99%）です。"
                            f"'30%' にフォールバックします。",
                            file=sys.stderr,
                        )
                except ValueError:
                    print(
                        f"警告: pip size '{value}' は数値として解釈できません。"
                        f"'30%' にフォールバックします。",
                        file=sys.stderr,
                    )
            else:
                # % なしは不正扱い
                print(
                    f"警告: pip size '{value}' に '%' がありません。"
                    f"'30%' にフォールバックします。",
                    file=sys.stderr,
                )

        elif key == "loop":
            if value == "false":
                loop = False
            elif value == "true":
                loop = True
            else:
                print(
                    f"警告: pip loop '{value}' は 'true'/'false' のいずれかである必要があります。"
                    f"'true' にフォールバックします。",
                    file=sys.stderr,
                )

        elif key == "pip_audio":
            if value == "true":
                pip_audio = True
            elif value == "false":
                pip_audio = False
            else:
                print(
                    f"警告: pip_audio '{value}' は 'true'/'false' のみ有効です。"
                    f"'false' にフォールバックします。",
                    file=sys.stderr,
                )

    return PipConfig(
        path=path,
        position=position,
        size_percent=size_percent,
        loop=loop,
        pip_audio=pip_audio,
    )


def parse_pip_directives(script_text: str) -> list[tuple[int, PipConfig | None]]:
    """台本テキストから pip ディレクティブを抽出する。

    Args:
        script_text: 台本の全テキスト

    Returns:
        (行番号, PipConfig | None) のリスト。
        None は <!-- pip: stop --> に対応する。

    Examples:
        >>> results = parse_pip_directives("<!-- pip: screen.mp4 -->")
        >>> results[0][1].position
        'bottom-right'
        >>> results[0][1].size_percent
        30

        >>> results = parse_pip_directives("<!-- pip: stop -->")
        >>> results[0][1] is None
        True
    """
    results = []
    for lineno, line in enumerate(script_text.splitlines(), start=1):
        stripped = line.strip()

        # <!-- pip: stop --> — PiP を終了する
        if re.match(r"<!--\s*pip:\s*stop\s*-->$", stripped):
            results.append((lineno, None))
            continue

        # <!-- pip: path [params...] --> — PiP を開始する
        m = re.match(r"<!--\s*pip:\s*(.+?)\s*-->$", stripped)
        if m:
            config = _parse_pip_directive(m.group(1))
            results.append((lineno, config))

    return results


# ──────────────────────────────────────────────
# セグメントビルダー: シーンリスト → PiP セグメントのタイムライン
# ──────────────────────────────────────────────

@dataclass
class Scene:
    """台本の1シーンを表す（デモ用の簡略モデル）。"""
    name: str
    duration: float  # 秒
    pip: PipConfig | None = None  # PiP 設定（None = PiP なし）


def build_pip_segments(
    scenes: list[Scene],
) -> list[tuple[PipConfig, float, float]]:
    """シーンリストから連続する PiP セグメントを構築する。

    同一 PipConfig が連続するシーンは1つのセグメントにまとめる。
    これにより、シーン境界でタイムコードがリセットされず、
    PiP 動画がシーンをまたいで連続再生される。

    Args:
        scenes: シーンのリスト（duration を持つ）

    Returns:
        (PipConfig, start_sec, end_sec) のリスト。
        start_sec / end_sec は動画全体の先頭からの秒数。

    Example:
        シーン1（5s, pip=A）+ シーン2（3s, pip=A）→ [(A, 0, 8)]
        シーン1（5s, pip=A）+ シーン2（3s, pip=B）→ [(A, 0, 5), (B, 5, 8)]
        シーン1（5s, pip=A）+ シーン2（3s, pip=None）→ [(A, 0, 5)]
    """
    segments: list[tuple[PipConfig, float, float]] = []
    current_pos = 0.0

    # 連続する同一 PipConfig をひとまとめにするため、前のシーンの情報を保持する
    seg_start: float | None = None
    seg_config: PipConfig | None = None

    for scene in scenes:
        scene_end = current_pos + scene.duration

        if scene.pip is None:
            # PiP なし: 進行中のセグメントがあれば閉じる
            if seg_config is not None:
                segments.append((seg_config, seg_start, current_pos))
                seg_config = None
                seg_start = None

        elif seg_config is None:
            # PiP あり（初回 or 再開）: 新しいセグメントを開始する
            seg_config = scene.pip
            seg_start = current_pos

        elif _pip_config_equals(scene.pip, seg_config):
            # PiP あり（同一設定）: セグメントを継続する（タイムコードは加算するだけ）
            pass

        else:
            # PiP あり（設定が変わった）: 前のセグメントを閉じて新しいセグメントを開始する
            segments.append((seg_config, seg_start, current_pos))
            seg_config = scene.pip
            seg_start = current_pos

        current_pos = scene_end

    # 末尾のセグメントを閉じる
    if seg_config is not None:
        segments.append((seg_config, seg_start, current_pos))

    return segments


def _pip_config_equals(a: PipConfig, b: PipConfig) -> bool:
    """2つの PipConfig が同一かどうかを比較する（path の文字列表現で比較）。"""
    return (
        str(a.path) == str(b.path)
        and a.position == b.position
        and a.size_percent == b.size_percent
        and a.loop == b.loop
        and a.pip_audio == b.pip_audio
    )


# ──────────────────────────────────────────────
# ffmpeg コマンド生成（実際には実行しない・概念説明用）
# ──────────────────────────────────────────────

def build_ffmpeg_pip_command(
    video_path: Path,
    segments: list[tuple[PipConfig, float, float]],
    output_path: Path,
    video_w: int = 1920,
) -> list[str]:
    """ffmpeg overlay コマンドを組み立てて返す（実行はしない）。

    position プリセットから ffmpeg の overlay 座標式（W, H, w, h 変数）に変換する。
    複数セグメントがある場合は filter_complex を連鎖させる。

    Args:
        video_path: 本編動画ファイル
        segments: (PipConfig, start_sec, end_sec) のリスト
        output_path: 出力先
        video_w: 本編動画の幅（px）。PiP サイズ計算（size_percent）に使う

    Returns:
        ffmpeg コマンドを表す文字列リスト
    """
    MARGIN = 20  # px（PiP ウィンドウと画面端の余白）

    # position プリセット → ffmpeg overlay 座標式
    # W・H は overlay フィルターのメインストリームの幅・高さ
    # w・h は overlay フィルターの overlay ストリームの幅・高さ
    position_map: dict[str, tuple[str, str]] = {
        "top-left":      (f"{MARGIN}", f"{MARGIN}"),
        "top-right":     (f"W-w-{MARGIN}", f"{MARGIN}"),
        "bottom-left":   (f"{MARGIN}", f"H-h-{MARGIN}"),
        "bottom-right":  (f"W-w-{MARGIN}", f"H-h-{MARGIN}"),
        "center":        ("(W-w)/2", "(H-h)/2"),
        "center-top":    ("(W-w)/2", f"{MARGIN}"),
        "center-bottom": ("(W-w)/2", f"H-h-{MARGIN}"),
        "left":          (f"{MARGIN}", "(H-h)/2"),
        "right":         (f"W-w-{MARGIN}", "(H-h)/2"),
    }

    if not segments:
        # PiP なし: そのままコピーするだけ
        return ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)]

    cmd = ["ffmpeg", "-y"]
    cmd += ["-i", str(video_path)]

    # 各セグメントの PiP 動画を入力に追加する
    for i, (cfg, start, end) in enumerate(segments):
        if cfg.loop:
            # loop=true: -stream_loop -1 は -i の直前に置く必要がある
            cmd += ["-stream_loop", "-1"]
        cmd += ["-i", str(cfg.path)]

    # filter_complex を組み立てる
    filter_parts: list[str] = []
    for i, (cfg, start, end) in enumerate(segments):
        pip_input_idx = i + 1  # 0 番目は本編動画
        pip_w = int(video_w * cfg.size_percent / 100)
        # -2 は H.264 の codec 要件（幅・高さが 2 の倍数でなければエラー）
        scale_h = -2

        x_expr, y_expr = position_map.get(cfg.position, (f"W-w-{MARGIN}", f"H-h-{MARGIN}"))
        t_start = f"{start:.6g}"
        t_end = f"{end:.6g}"

        if cfg.loop:
            # loop=true: そのままスケールして overlay
            scale_filter = (
                f"[{pip_input_idx}:v]"
                f"scale={pip_w}:{scale_h}:force_original_aspect_ratio=decrease"
                f"[pip_scaled{i}]"
            )
        else:
            # loop=false: tpad で末尾フレームを無限複製して最終フレーム静止を実現する
            scale_filter = (
                f"[{pip_input_idx}:v]"
                f"tpad=stop=-1:stop_mode=clone,"
                f"scale={pip_w}:{scale_h}:force_original_aspect_ratio=decrease"
                f"[pip_scaled{i}]"
            )

        in_label = "[0:v]" if i == 0 else f"[v{i}]"
        out_label = "[vout]" if i == len(segments) - 1 else f"[v{i + 1}]"

        overlay_filter = (
            f"{in_label}[pip_scaled{i}]"
            f"overlay=x={x_expr}:y={y_expr}"
            f":enable='between(t,{t_start},{t_end})'"
            f"{out_label}"
        )

        filter_parts.append(scale_filter)
        filter_parts.append(overlay_filter)

    cmd += ["-filter_complex", "; ".join(filter_parts)]
    cmd += ["-map", "[vout]", "-map", "0:a"]
    cmd += ["-c:a", "copy", "-c:v", "libx264", "-preset", "fast"]
    cmd += [str(output_path)]

    return cmd


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

SAMPLE_SCRIPT = """\
## scene1: 導入

<!-- speaker: yumu -->
ここから PiP なしで説明を始めます。

## scene2: デモ開始

<!-- speaker: yumu -->
<!-- pip: inputs/episodes/ep3.6/screen_recording.mp4 position=bottom-right size=35% -->
右下にスクリーン録画が表示されます。セクションをまたいでも引き継がれます。

## scene3: 解説続き

<!-- speaker: sabacyan -->
pip ディレクティブを再度書かなくても、そのまま PiP が続きます。

## scene4: 音声付きデモ

<!-- speaker: yumu -->
<!-- pip: inputs/episodes/ep3.6/demo_with_audio.mp4 position=bottom-right size=35% pip_audio=true -->
別の pip を書くと上書きされます。pip_audio=true で PiP の音声もミックスされます。

## scene5: デモ終了

<!-- speaker: sabacyan -->
<!-- pip: stop -->
ここから PiP が消えます。通常のアバターシーンに戻ります。
"""

SAMPLE_DIALOGUE_AVATAR_AREA_SCRIPT = """\
## scene1: 2人で鑑賞

<!-- config: layout=dialogue -->
<!-- config: dialogue_avatar_area=left -->
<!-- pip: inputs/episodes/ep3.6/screen_recording.mp4 position=right size=45% -->
キャラを左半分に寄せて、右半分にスクリーン録画を表示します。
「2人で鑑賞」の構図が作れます。
"""


def cmd_parse() -> None:
    """台本サンプルから pip ディレクティブを抽出して表示する。"""
    print("─── 台本サンプル（PiP 基本） ───")
    print(SAMPLE_SCRIPT)
    print("─── 抽出された PipConfig ───")
    results = parse_pip_directives(SAMPLE_SCRIPT)
    if not results:
        print("pip ディレクティブが見つかりませんでした")
        return

    for lineno, config in results:
        if config is None:
            print(f"  行{lineno:3d}: pip: stop  → None（PiP 終了）")
        else:
            print(
                f"  行{lineno:3d}: pip: {config.path}"
                f"  position={config.position}"
                f"  size={config.size_percent}%"
                f"  loop={config.loop}"
                f"  pip_audio={config.pip_audio}"
            )

    print()
    print("─── dialogue_avatar_area との組み合わせ例 ───")
    print(SAMPLE_DIALOGUE_AVATAR_AREA_SCRIPT)
    print("─── 抽出された PipConfig ───")
    results2 = parse_pip_directives(SAMPLE_DIALOGUE_AVATAR_AREA_SCRIPT)
    for lineno, config in results2:
        if config is None:
            print(f"  行{lineno:3d}: pip: stop  → None")
        else:
            print(
                f"  行{lineno:3d}: pip: {config.path}"
                f"  position={config.position}"
                f"  size={config.size_percent}%"
                f"  loop={config.loop}"
                f"  pip_audio={config.pip_audio}"
            )
    print()
    print("  ポイント: dialogue_avatar_area=left でキャラが左半分に寄り、")
    print("  position=right の PiP と「2人で鑑賞」の構図になります。")


def cmd_segment() -> None:
    """シーンリストから PiP セグメントを構築して表示する。"""
    # テスト用のシーンを用意する
    pip_a = PipConfig(path=Path("screen.mp4"), position="bottom-right", size_percent=35)
    pip_b = PipConfig(path=Path("demo.mp4"), position="bottom-right", size_percent=35, pip_audio=True)

    scenes = [
        Scene(name="scene1: 導入",         duration=4.0, pip=None),
        Scene(name="scene2: デモ開始",     duration=5.0, pip=pip_a),
        Scene(name="scene3: 解説続き",     duration=6.0, pip=pip_a),  # 同一 → 継続
        Scene(name="scene4: 音声付きデモ", duration=5.0, pip=pip_b),  # 別設定 → 新セグメント
        Scene(name="scene5: デモ終了",     duration=4.0, pip=None),   # None → 終了
    ]

    print("─── シーン構成 ───")
    for scene in scenes:
        pip_info = "なし" if scene.pip is None else f"pip={scene.pip.path} ({scene.pip.size_percent}%)"
        print(f"  {scene.name:<25}  duration={scene.duration:.1f}s  {pip_info}")
    total = sum(s.duration for s in scenes)
    print(f"  合計: {total:.1f}s")

    print()
    segments = build_pip_segments(scenes)
    print("─── _build_pip_segments の結果 ───")
    print("  シーンをまたいで同一 PipConfig が連続する区間をひとまとめにします。")
    print("  タイムコードが引き継がれるため、PiP 動画がシーン境界でリセットされません。")
    print()
    if not segments:
        print("  PiP セグメントなし")
    else:
        for i, (cfg, start, end) in enumerate(segments):
            print(
                f"  セグメント{i + 1}: {cfg.path}"
                f"  [{start:.1f}s → {end:.1f}s]"
                f"  position={cfg.position}"
                f"  loop={cfg.loop}"
                f"  pip_audio={cfg.pip_audio}"
            )

    print()
    print("─── 生成される ffmpeg コマンド（概念） ───")
    cmd = build_ffmpeg_pip_command(
        video_path=Path("output/video.mp4"),
        segments=segments,
        output_path=Path("output/pip.mp4"),
        video_w=1920,
    )
    # コマンドを見やすく折り返して表示する
    print("  ffmpeg \\")
    for token in cmd[1:]:
        if token.startswith("-"):
            print(f"    {token} \\")
        else:
            print(f"    '{token}' \\")


def main() -> None:
    parser = argparse.ArgumentParser(description="PiP ディレクティブ デモ")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("parse",   help="ディレクティブのパース結果を表示する")
    sub.add_parser("segment", help="セグメント合成の概念を表示する")

    args = parser.parse_args()

    if args.command == "parse":
        cmd_parse()
    elif args.command == "segment":
        cmd_segment()
    else:
        # 引数なし: 全デモを実行する
        print("=" * 60)
        print("PiP ディレクティブ デモ（全実行）")
        print("=" * 60)
        print()
        print("【1. パース】")
        cmd_parse()
        print()
        print("【2. セグメント合成】")
        cmd_segment()


if __name__ == "__main__":
    main()
