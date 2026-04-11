"""
SadTalker PiP 切り替えデモ

shorts/jissya-hayakuchi で使ったパターンを示す：
  1. 音声付き・1回再生  （pip_audio=true  loop=false）
  2. 無音ループ切り替え（pip_audio=false loop=true）

このスクリプトは実際に動画を生成しません。
台本のパース結果と PiP セグメントの構成をターミナルに出力します。
"""

from __future__ import annotations
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------

@dataclass
class PipConfig:
    path: str
    position: str = "bottom-right"
    size: str = "30%"
    loop: bool = True
    pip_audio: bool = False
    z_order: str = "front"  # "front" | "back"

    def __str__(self) -> str:
        return (
            f"PipConfig(path={self.path!r}, position={self.position!r}, "
            f"size={self.size!r}, loop={self.loop}, "
            f"pip_audio={self.pip_audio}, z_order={self.z_order!r})"
        )


@dataclass
class Scene:
    id: str
    narration: str
    pip: PipConfig | None = None
    pause: float = 0.0
    duration: float = 0.0  # narration + pause

    def __str__(self) -> str:
        pip_str = str(self.pip) if self.pip else "None"
        return (
            f"Scene(id={self.id!r}, narration={self.narration!r}, "
            f"duration={self.duration:.1f}s, pip={pip_str})"
        )


# ---------------------------------------------------------------------------
# パーサー
# ---------------------------------------------------------------------------

def parse_pip_directive(line: str) -> PipConfig | None:
    """
    <!-- pip: path [key=value ...] --> をパースして PipConfig を返す。
    pip でなければ None。
    """
    line = line.strip()
    if not (line.startswith("<!-- pip:") and line.endswith("-->")):
        return None

    content = line[len("<!-- pip:"):].rstrip("-->").strip()
    parts = content.split()
    if not parts:
        return None

    path = parts[0]
    kwargs: dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            k, v = part.split("=", 1)
            kwargs[k] = v

    def to_bool(s: str) -> bool:
        return s.lower() in ("true", "1", "yes")

    return PipConfig(
        path=path,
        position=kwargs.get("position", "bottom-right"),
        size=kwargs.get("size", "30%"),
        loop=to_bool(kwargs.get("loop", "true")),
        pip_audio=to_bool(kwargs.get("pip_audio", "false")),
        z_order=kwargs.get("z_order", "front"),
    )


# ---------------------------------------------------------------------------
# サンプル台本（jissya-hayakuchi の PiP 関連シーンのみ抜粋）
# ---------------------------------------------------------------------------

SCRIPT_SCENES: list[Scene] = [
    Scene(
        id="S01",
        narration="アニメキャラって、AIには顔に見えないらしくて。だから、実写の人に動いてもらいました。",
        pip=None,
        duration=4.0,
    ),
    Scene(
        id="S02",
        narration="（無音・SadTalker 動画を最後まで再生）",
        pip=PipConfig(
            path="output/test/sadtalker-hayakuchi/2026_04_03_15.10.36.mp4",
            position="top-right",
            size="80%",
            loop=False,       # 1回だけ再生
            pip_audio=True,   # PiP の音声をミックス
            z_order="back",   # アバターの背面に表示
        ),
        pause=5.5,
        duration=5.5,
    ),
    Scene(
        id="S02b",
        narration="……え。",
        pip=PipConfig(
            path="output/test/sadtalker-hayakuchi/2026_04_03_15.10.36.mp4",
            position="top-right",
            size="80%",
            loop=False,
            pip_audio=True,
            z_order="back",
        ),
        pause=1.5,
        duration=2.5,
    ),
    Scene(
        id="S03",
        narration="口パクがちゃんと動きました。",
        pip=PipConfig(
            path="output/test/sadtalker-hayakuchi/2026_04_03_15.10.36.mp4",
            position="top-right",
            size="80%",
            loop=True,        # 無音ループに切り替え
            pip_audio=False,
            z_order="back",
        ),
        duration=3.0,
    ),
]


# ---------------------------------------------------------------------------
# PiP セグメント構築
# ---------------------------------------------------------------------------

@dataclass
class PipSegment:
    config: PipConfig
    start: float
    end: float

    def __str__(self) -> str:
        return (
            f"  [{self.start:.1f}s - {self.end:.1f}s] "
            f"pip_audio={self.config.pip_audio} loop={self.config.loop} "
            f"z_order={self.config.z_order!r} size={self.config.size}"
        )


def build_pip_segments(scenes: list[Scene]) -> list[PipSegment]:
    """
    シーンリストを走査して PiP セグメントのタイムラインを構築する。

    同じ PipConfig が続く間はセグメントを結合する。
    config が変わった時点で前のセグメントを閉じて新しいセグメントを開始する。
    """
    segments: list[PipSegment] = []
    t = 0.0
    current_pip: PipConfig | None = None
    seg_start = 0.0

    for scene in scenes:
        if scene.pip != current_pip:
            # 前のセグメントを閉じる
            if current_pip is not None:
                segments.append(PipSegment(current_pip, seg_start, t))
            current_pip = scene.pip
            seg_start = t
        t += scene.duration

    # 最後のセグメントを閉じる
    if current_pip is not None:
        segments.append(PipSegment(current_pip, seg_start, t))

    return segments


# ---------------------------------------------------------------------------
# ffmpeg コマンド生成（概念デモ）
# ---------------------------------------------------------------------------

def generate_ffmpeg_command(input_video: str, segments: list[PipSegment]) -> str:
    """
    PiP セグメントから ffmpeg overlay コマンドの概要を生成する（実行可能な形式ではない）。
    """
    lines = ["ffmpeg \\", f"  -i {input_video} \\"]
    for i, seg in enumerate(segments):
        lines.append(f"  -i {seg.config.path} \\  # segment {i}: pip_audio={seg.config.pip_audio}")

    lines.append("  -filter_complex '")
    for i, seg in enumerate(segments):
        overlay_pos = "[pip_pos]"
        z_filter = "overlay=x=W-w-10:y=10" if seg.config.z_order == "front" else "overlay=x=W-w-10:y=10:shortest=1"
        lines.append(f"    # segment {i} ({seg.start:.1f}s-{seg.end:.1f}s): {z_filter},")
    lines.append("  '")
    lines.append("  output_with_pip.mp4")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("SadTalker PiP 切り替えデモ — shorts/jissya-hayakuchi")
    print("=" * 60)

    print("\n--- シーン一覧 ---")
    for scene in SCRIPT_SCENES:
        print(f"  {scene}")

    print("\n--- PiP セグメント（タイムライン） ---")
    segments = build_pip_segments(SCRIPT_SCENES)
    for seg in segments:
        print(seg)

    total = sum(s.duration for s in SCRIPT_SCENES)
    print(f"\n  合計時間: {total:.1f}s")

    print("\n--- PiP 切り替えパターンの確認 ---")
    audio_on = [s for s in segments if s.config.pip_audio]
    audio_off = [s for s in segments if not s.config.pip_audio]
    print(f"  音声付き区間: {len(audio_on)} セグメント")
    print(f"  無音ループ区間: {len(audio_off)} セグメント")

    if audio_on:
        first = audio_on[0]
        print(f"\n  [音声付き] {first.start:.1f}s - {first.end:.1f}s  ← SadTalker 音声を本編にミックス")
    if audio_off:
        last = audio_off[-1]
        print(f"  [無音ループ] {last.start:.1f}s - {last.end:.1f}s  ← 解説中はループ・無音")

    print("\n--- ffmpeg コマンドイメージ ---")
    print(generate_ffmpeg_command("main.mp4", segments))

    print("\n完了。")


if __name__ == "__main__":
    main()
