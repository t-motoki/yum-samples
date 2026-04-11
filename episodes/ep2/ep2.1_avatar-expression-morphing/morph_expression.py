"""
THA3（Talking Head Anime 3）で立ち絵の表情を変形する（失敗実録）

動画「同一キャラクターの表情だけを変える — 表情モーフィング再挑戦」のサンプルです。
このコードは動画内で実際に試したものです。ゆむの立ち絵では期待通りに動きませんでした。
なぜ失敗したかは動画の失敗分析シーンをご覧ください。

前提:
  pip install talking-head-anime-3-demo torch pillow
  モデルファイルを別途ダウンロードして ./tha3_models/ に配置すること
  → 手順: https://github.com/pkhungurn/talking-head-anime-3-demo

使い方:
  python morph_expression.py avatar_rgba.png
  → output/ に joy.png, angry.png, thinking.png が生成される
"""

import sys
from pathlib import Path

import torch
from PIL import Image

# 利用可能なモデル種別（tha3_models/ に対応ファイルが必要）
MODEL_DIR = Path("tha3_models")

# 表情パラメータ（45次元ポーズベクトルの一部）
# 各値は -1.0〜1.0 の範囲で表情を指定する
EXPRESSIONS = {
    "joy": {
        "mouth_open":  0.8,   # 口を開く
        "eye_wink_l":  0.3,   # 左目を細める
        "eye_wink_r":  0.3,   # 右目を細める
        "brow_lowerer": -0.3, # 眉を上げる（負値で上方向）
    },
    "angry": {
        "brow_lowerer": 0.8,  # 眉を下げる
        "eye_open_l":   0.5,  # 目を見開く
        "eye_open_r":   0.5,
        "mouth_open":  -0.2,  # 口をへの字に
    },
    "thinking": {
        "eye_wink_l":   0.5,  # 片目を細める
        "brow_lowerer": 0.2,  # 眉をわずかに下げる
    },
}


def load_image(path: str) -> torch.Tensor:
    """RGBA PNG を THA3 が期待するテンソル形式に変換する"""
    img = Image.open(path).convert("RGBA").resize((512, 512))
    import numpy as np
    arr = np.array(img).astype(np.float32) / 255.0

    # sRGB → linear 変換（ここを省略すると全画像が同じ出力になる: 失敗①）
    rgb = arr[:, :, :3]
    rgb = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    arr[:, :, :3] = rgb

    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)  # (1, C, H, W)
    return tensor


def build_pose_vector(expression: dict) -> torch.Tensor:
    """表情パラメータ辞書から 45 次元ポーズベクトルを生成する"""
    # THA3 のポーズベクトルのインデックス定義（主要なもの）
    PARAM_INDEX = {
        "eye_wink_l":   0,
        "eye_wink_r":   1,
        "eye_open_l":   2,
        "eye_open_r":   3,
        "brow_lowerer": 4,
        "mouth_open":   5,
    }
    pose = torch.zeros(1, 45)
    for key, value in expression.items():
        if key in PARAM_INDEX:
            pose[0, PARAM_INDEX[key]] = value
    return pose


def morph(avatar_path: str, output_dir: str = "output") -> None:
    if not MODEL_DIR.exists():
        print(f"エラー: {MODEL_DIR}/ にモデルファイルが見つかりません")
        print("→ https://github.com/pkhungurn/talking-head-anime-3-demo を参照してください")
        return

    device = torch.device("cpu")  # GPU 不要
    print(f"デバイス: {device}")

    # モデルのロード（talking-head-anime-3-demo の Poser クラスを使用）
    try:
        from tha3.poser.poser import Poser
        from tha3.util import torch_load_model
        poser: Pose = torch_load_model(MODEL_DIR / "separable_float", device)
    except ImportError:
        print("エラー: tha3 がインストールされていません")
        print("→ pip install talking-head-anime-3-demo")
        return

    source = load_image(avatar_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for name, params in EXPRESSIONS.items():
        print(f"生成中: {name} ...")
        pose = build_pose_vector(params)
        with torch.no_grad():
            output_tensor = poser.pose(source, pose)[0]

        # linear → sRGB 逆変換
        import numpy as np
        arr = output_tensor.squeeze(0).permute(1, 2, 0).numpy()
        rgb = arr[:, :, :3]
        rgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * (rgb ** (1 / 2.4)) - 0.055)
        arr[:, :, :3] = np.clip(rgb, 0, 1)
        result = Image.fromarray((arr * 255).astype("uint8"), mode="RGBA")

        output_path = out / f"{name}.png"
        result.save(output_path)
        print(f"  → {output_path}")

    print("\n完了")
    print("※ 全部ほぼ同じ顔になった場合は動画の失敗分析シーンを参照してください")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python morph_expression.py <avatar_rgba.png>")
        sys.exit(1)
    morph(sys.argv[1])
