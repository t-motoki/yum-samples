"""
ep3.5.6 サンプル: テロップエフェクトディレクティブ

台本に <!-- telop_effect: xxx --> と書くだけで、テロップの表示アニメーションを
4種類から選べる仕組みのデモ。

台本での書き方:
  <!-- telop_effect: typewriter -->      # 文字が左から1文字ずつ出てくる
  <!-- telop_effect: slide-in -->        # テロップが下からスライドして入る
  <!-- telop_effect: bounce -->          # テロップが弾んで出てくる
  <!-- telop_effect: highlight-word -->  # 指定単語を黄色でハイライト
  <!-- telop_highlight: 単語1, 単語2 --> # ハイライト対象の単語を指定

スコープ: セクション（##）単位。またいでは引き継がれない。

必要なもの:
  pip install pillow numpy

使い方:
  # 4種類のエフェクトをフレーム画像として出力して比較する
  python telop_effect_demo.py render --text "テロップのアニメーションをテストします"

  # typewriter の各フレームを t=0〜1.0 秒で出力する
  python telop_effect_demo.py render --effect typewriter --text "タイプライターのデモ"

  # highlight-word で単語をハイライトする
  python telop_effect_demo.py render --effect highlight-word --text "重要な単語を強調する" --words "重要"

  # パーサーの動作を確認する（画像出力なし）
  python telop_effect_demo.py parse
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
except ImportError:
    print("必要なライブラリが見つかりません。以下を実行してください:")
    print("  pip install pillow numpy")
    sys.exit(1)


# ────────────────────────────────────────────────
# 定数
# ────────────────────────────────────────────────

VIDEO_W, VIDEO_H = 1920, 1080
TELOP_BAR_H = 130
TELOP_BAR_Y = VIDEO_H - TELOP_BAR_H
TELOP_PADDING_X = 40
TELOP_FONT_SIZE = 42
TELOP_BG = (20, 20, 20)
TELOP_BAR_ALPHA = 200
ACCENT_COLOR = (100, 180, 255)

EFFECT_DURATION_SEC = 1.0   # エフェクト持続時間（全エフェクト共通）
HIGHLIGHT_COLOR = (255, 215, 0)  # #FFD700（ゴールド）


# ────────────────────────────────────────────────
# 値オブジェクト
# ────────────────────────────────────────────────

VALID_EFFECTS = {"typewriter", "slide-in", "highlight-word", "bounce", "fade"}


@dataclass
class TelopEffectConfig:
    """テロップ表示アニメーションの設定を保持する値オブジェクト。

    effect: エフェクト種別
    highlight_words: highlight-word エフェクト時にハイライトする単語リスト
    """
    effect: str
    highlight_words: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.effect not in VALID_EFFECTS:
            raise ValueError(f"effect は {VALID_EFFECTS} のいずれかである必要があります: {self.effect!r}")


# ────────────────────────────────────────────────
# パーサー（台本 Markdown → TelopEffectConfig）
# ────────────────────────────────────────────────

import re


def parse_telop_directives(markdown: str) -> list[dict]:
    """台本から <!-- telop_effect: xxx --> / <!-- telop_highlight: ... --> をパースする。

    戻り値: [{"text": str, "effect": TelopEffectConfig | None}, ...]
    """
    results = []
    current_effect: TelopEffectConfig | None = None
    current_highlight_words: list[str] = []

    for line in markdown.splitlines():
        stripped = line.strip()

        # セクション切り替えでリセット
        if stripped.startswith("## "):
            current_effect = None
            current_highlight_words = []
            continue

        # <!-- telop_effect: xxx -->
        m = re.match(r"<!--\s*telop_effect:\s*(\S+?)\s*-->$", stripped)
        if m:
            value = m.group(1)
            if value in VALID_EFFECTS:
                current_effect = TelopEffectConfig(effect=value, highlight_words=current_highlight_words[:])
            else:
                print(f"警告: 不明な telop_effect 値 '{value}' はスキップします", file=sys.stderr)
                current_effect = None
            continue

        # <!-- telop_highlight: word1, word2 -->
        m = re.match(r"<!--\s*telop_highlight:\s*(.+?)\s*-->$", stripped)
        if m:
            current_highlight_words = [w.strip() for w in m.group(1).split(",") if w.strip()]
            if current_effect is not None:
                current_effect = TelopEffectConfig(
                    effect=current_effect.effect,
                    highlight_words=current_highlight_words[:],
                )
            continue

        # ナレーション行（ディレクティブ以外の非空行）
        if stripped and not stripped.startswith("<!--") and not stripped.startswith("#") and stripped != "---":
            results.append({"text": stripped, "effect": current_effect})

    return results


# ────────────────────────────────────────────────
# レンダラー
# ────────────────────────────────────────────────

def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """日本語フォントを読み込む。見つからなければデフォルトフォントを使う。"""
    font_candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
    ]
    for path in font_candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_telop_frame(
    text: str,
    t: float,
    effect: TelopEffectConfig | None = None,
    fade_sec: float = 0.5,
) -> Image.Image:
    """テロップバーを描画したフレームを返す。

    t: シーン内経過秒（0.0〜）
    effect: None のとき既存の fade 動作
    """
    frame = Image.new("RGB", (VIDEO_W, VIDEO_H), (30, 30, 50))  # 背景（暗い青）
    _draw_telop_bar(frame, text, t, effect, fade_sec)
    return frame


def _draw_telop_bar(
    frame: Image.Image,
    text: str,
    t: float,
    effect: TelopEffectConfig | None,
    fade_sec: float,
) -> None:
    from PIL import ImageChops

    w, h = frame.size
    telop_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(telop_layer)
    font = _load_font(TELOP_FONT_SIZE)

    if effect is None or effect.effect == "fade":
        _render_fade(draw, font, text, t, fade_sec, w, h)
    elif effect.effect == "typewriter":
        _render_typewriter(draw, font, text, t, w, h)
    elif effect.effect == "slide-in":
        _render_slide_in(draw, font, text, t, w, h)
    elif effect.effect == "highlight-word":
        _render_highlight_word(draw, font, text, effect.highlight_words, w, h)
    elif effect.effect == "bounce":
        _render_bounce(draw, font, text, t, w, h)

    frame_rgba = frame.convert("RGBA")
    frame_rgba.alpha_composite(telop_layer)
    frame.paste(frame_rgba.convert("RGB"))


def _draw_bar_and_text(draw, font, text, w, h, y_offset=0, alpha=1.0):
    """バー・アクセントライン・テキストを描画する共通処理。y_offset で位置をずらせる。"""
    bar_y = TELOP_BAR_Y + y_offset
    bar_alpha = int(TELOP_BAR_ALPHA * alpha)
    text_alpha = int(255 * alpha)

    draw.rectangle([(0, bar_y), (w - 1, h - 1 + y_offset)], fill=TELOP_BG + (bar_alpha,))
    draw.line([(0, bar_y), (w, bar_y)], fill=ACCENT_COLOR + (255,), width=3)

    if text:
        lines = _wrap_text(draw, text, font, w - TELOP_PADDING_X * 2)[:2]
        line_h = TELOP_FONT_SIZE + 8
        total_h = len(lines) * line_h
        y = bar_y + (TELOP_BAR_H - total_h) // 2

        for line in lines:
            for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                draw.text((TELOP_PADDING_X + dx, y + dy), line, font=font, fill=(0, 0, 0, text_alpha))
            draw.text((TELOP_PADDING_X, y), line, font=font, fill=(255, 255, 255, text_alpha))
            y += line_h


def _wrap_text(draw, text, font, max_w):
    lines, current = [], ""
    for ch in text:
        test = current + ch
        if draw.textlength(test, font=font) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def _render_fade(draw, font, text, t, fade_sec, w, h):
    alpha = min(t / fade_sec, 1.0) if fade_sec > 0 else 1.0
    _draw_bar_and_text(draw, font, text, w, h, alpha=alpha)


def _render_typewriter(draw, font, text, t, w, h):
    duration = min(len(text) * 0.07, EFFECT_DURATION_SEC)
    n = len(text) if t >= duration else max(1, math.floor(len(text) * t / duration)) if duration > 0 else len(text)
    display = text[:n]
    _draw_bar_and_text(draw, font, display, w, h, alpha=1.0)


def _render_slide_in(draw, font, text, t, w, h):
    progress = min(t / EFFECT_DURATION_SEC, 1.0)
    # ease-out: 終盤ほど滑らか
    eased = 1.0 - (1.0 - progress) ** 2
    y_offset = int(TELOP_BAR_H * (1.0 - eased))
    _draw_bar_and_text(draw, font, text, w, h, y_offset=y_offset, alpha=1.0)


def _render_bounce(draw, font, text, t, w, h):
    if t >= EFFECT_DURATION_SEC:
        y_offset = 0
    else:
        A, k, omega = 30.0, 4.0, 12.0
        y_offset = int(A * math.exp(-k * t) * math.sin(omega * t + math.pi / 2))
    _draw_bar_and_text(draw, font, text, w, h, y_offset=y_offset, alpha=1.0)


def _render_highlight_word(draw, font, text, highlight_words, w, h):
    _draw_bar_and_text(draw, font, text, w, h, alpha=1.0)

    if not highlight_words or not text:
        return

    # ハイライト: 単語の X 範囲を検出して黄色で上書き
    lines = _wrap_text(draw, text, font, w - TELOP_PADDING_X * 2)[:2]
    line_h = TELOP_FONT_SIZE + 8
    total_h = len(lines) * line_h
    y = TELOP_BAR_Y + (TELOP_BAR_H - total_h) // 2

    for line in lines:
        x = TELOP_PADDING_X
        for word in highlight_words:
            idx = line.find(word)
            while idx != -1:
                x_start = x + int(draw.textlength(line[:idx], font=font))
                x_end = x_start + int(draw.textlength(word, font=font))
                # 黄色背景
                draw.rectangle([(x_start - 2, y - 2), (x_end + 2, y + TELOP_FONT_SIZE + 2)],
                                fill=HIGHLIGHT_COLOR + (200,))
                # 黒テキスト（視認性向上）
                draw.text((x_start, y), word, font=font, fill=(0, 0, 0, 255))
                idx = line.find(word, idx + 1)
        y += line_h


# ────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────

def cmd_render(args):
    """各エフェクトのフレームを output/ に PNG として出力する。"""
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    effects = [args.effect] if args.effect else ["typewriter", "slide-in", "bounce", "highlight-word", None]
    t_values = [0.0, 0.3, 0.6, 1.0, 2.0]

    for effect_name in effects:
        if effect_name is not None:
            cfg = TelopEffectConfig(
                effect=effect_name,
                highlight_words=[w.strip() for w in args.words.split(",")] if args.words else [],
            )
        else:
            cfg = None

        label = effect_name or "fade"
        print(f"\n[{label}] フレームを出力中...")
        for t in t_values:
            frame = render_telop_frame(args.text, t, cfg)
            out_path = out_dir / f"{label}_t{t:.1f}.png"
            frame.save(out_path)
            print(f"  → {out_path}")

    print(f"\n完了。{out_dir}/ に PNG が出力されました。")


def cmd_parse(args):
    """サンプル台本のパース結果を表示する。"""
    sample_md = """\
# テロップエフェクトのデモ

## scene1: typewriter
<!-- telop_effect: typewriter -->
タイプライターで文字が出てきます。

## scene2: highlight-word
<!-- telop_effect: highlight-word -->
<!-- telop_highlight: 重要, エフェクト -->
重要な単語にエフェクトをつけます。

## scene3: bounce
<!-- telop_effect: bounce -->
弾んで出てきます。

## scene4: エフェクトなし
デフォルトの表示です。
"""
    results = parse_telop_directives(sample_md)
    print("パース結果:")
    for r in results:
        effect_str = f"{r['effect'].effect}" if r['effect'] else "None（デフォルト）"
        words_str = f" words={r['effect'].highlight_words}" if r['effect'] and r['effect'].highlight_words else ""
        print(f"  text={r['text'][:30]!r}  effect={effect_str}{words_str}")


def main():
    parser = argparse.ArgumentParser(description="ep3.5.6 テロップエフェクトデモ")
    sub = parser.add_subparsers(dest="command")

    r = sub.add_parser("render", help="フレーム画像を出力する")
    r.add_argument("--text", default="テロップのアニメーションをテストします", help="テロップテキスト")
    r.add_argument("--effect", choices=list(VALID_EFFECTS), default=None,
                   help="エフェクト名（省略時は全種類出力）")
    r.add_argument("--words", default=None, help="ハイライト単語（カンマ区切り）")

    sub.add_parser("parse", help="台本パースのデモ")

    args = parser.parse_args()
    if args.command == "render":
        cmd_render(args)
    elif args.command == "parse":
        cmd_parse(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
