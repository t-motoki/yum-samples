"""
テロップフェードインアニメーションのデモ

動画「テロップフェードインアニメーション — 静止テロップに「動き」を加える」のサンプルです。

ep3.0 で作ったパイプラインに「テロップをフワッと出す」演出を追加する仕組みを
Pillow だけで動かせるデモとして切り出しています。

前提:
  pip install pillow

使い方:
  python telop_fade_demo.py
  → output/ に before.png / after_00.png〜after_09.png が生成される
     before: テロップが突然出現する（フェードなし）
     after:  0.3秒かけてフェードインする（各フレームを出力）
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --- キャンバス設定 ---
W, H = 1280, 720
TELOP_H = 80          # テロップバーの高さ
TELOP_Y = H - TELOP_H - 20  # テロップバーの上端 Y 座標
FPS = 30              # フレームレート
FADE_SEC = 0.3        # フェードイン秒数


def draw_frame(text: str, alpha: float = 1.0) -> Image.Image:
    """1フレームを生成する。alpha=1.0 が完全表示、0.0 が完全透明。"""
    # 背景（グレー）
    frame = Image.new("RGB", (W, H), color=(40, 40, 50))
    draw = ImageDraw.Draw(frame)

    # アバター代わりの円（実際のパイプラインではここにゆむの画像が入る）
    draw.ellipse([(W // 2 - 120, H // 2 - 200, W // 2 + 120, H // 2 + 200)],
                 fill=(200, 180, 160))

    # テロップバー（半透明の黒帯）
    # alpha を反映した不透明度でオーバーレイする
    bar_opacity = int(180 * alpha)  # 0〜180 の範囲で変化
    bar = Image.new("RGBA", (W, TELOP_H), (0, 0, 0, bar_opacity))
    frame_rgba = frame.convert("RGBA")
    frame_rgba.paste(bar, (0, TELOP_Y), mask=bar)

    # テロップ文字
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except OSError:
        font = ImageFont.load_default()

    text_opacity = int(255 * alpha)
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_draw.text((W // 2, TELOP_Y + TELOP_H // 2), text,
                   fill=(255, 255, 255, text_opacity),
                   font=font, anchor="mm")
    frame_rgba = Image.alpha_composite(frame_rgba, text_layer)

    return frame_rgba.convert("RGB")


def calc_fade_alpha(t: float, fade_sec: float) -> float:
    """
    フェードイン透明度を計算する。

    これが ep3.1 の核心となる式です。
      - t: シーン開始からの経過時刻（秒）
      - fade_sec: フェードイン完了までの秒数
      - 戻り値: 0.0（透明）〜 1.0（不透明）

    fade_sec=0 のときは常に 1.0 を返す（アニメーションなし＝before の動作）。
    """
    if fade_sec <= 0:
        return 1.0
    return min(t / fade_sec, 1.0)


def main() -> None:
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)

    text = "テロップフェードインのデモです"

    # --- before: フェードなし（突然出現）---
    before = draw_frame(text, alpha=1.0)
    before.save(out / "before.png")
    print("保存: output/before.png（フェードなし・突然出現）")

    # --- after: 0.3秒かけてフェードイン（10フレーム分）---
    n_frames = int(FADE_SEC * FPS)  # 0.3秒 × 30fps = 9フレーム
    for i in range(n_frames + 1):
        t = i / FPS
        alpha = calc_fade_alpha(t, FADE_SEC)
        frame = draw_frame(text, alpha=alpha)
        path = out / f"after_{i:02d}.png"
        frame.save(path)
        print(f"保存: {path}  (t={t:.3f}s, alpha={alpha:.2f})")

    print(f"\n完了: output/ に before + {n_frames + 1} フレームを生成しました")
    print("before.png と after_09.png を並べて比較してみてください")


if __name__ == "__main__":
    main()
