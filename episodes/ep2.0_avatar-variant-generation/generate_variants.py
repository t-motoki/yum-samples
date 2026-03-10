"""
IP-Adapterで表情バリエーションを生成する（失敗実録）

動画「IP-Adapterで1枚のアバターから表情バリエーションを生成する（失敗実録）」のサンプルです。
このコードは動画内で実際に実行したものです。結果がどうなったかは動画をご覧ください。

前提:
  pip install diffusers transformers accelerate torch pillow

使い方:
  python generate_variants.py avatar.png
  → output/ に joy.png, thinking.png, angry.png, pointing.png, nod.png が生成される
"""

import sys
from pathlib import Path

from diffusers import StableDiffusionPipeline
from PIL import Image

EXPRESSIONS = {
    "joy":      "smiling, happy, anime style",
    "thinking": "finger on chin, thinking, anime style",
    "angry":    "frowning, angry, anime style",
    "pointing": "pointing forward, anime style",
    "nod":      "nodding, gentle smile, anime style",
}

BASE_PROMPT = "1girl, white background, full body, standing"
NEGATIVE_PROMPT = "nsfw, lowres, bad anatomy, extra limbs"


def generate_variants(reference_path: str, output_dir: str = "output") -> None:
    reference = Image.open(reference_path).convert("RGB")

    print("モデルを読み込んでいます（初回は数分かかります）...")
    pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models", weight_name="ip-adapter_sd15.bin")
    pipe.set_ip_adapter_scale(0.6)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for name, expression_prompt in EXPRESSIONS.items():
        print(f"生成中: {name} ...")
        prompt = f"{BASE_PROMPT}, {expression_prompt}"
        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            ip_adapter_image=reference,  # このキャラクターを参照しながら生成
            num_inference_steps=30,
        ).images[0]

        output_path = out / f"{name}.png"
        result.save(output_path)
        print(f"  → {output_path}")

    print(f"\n完了: {output_dir}/ に {len(EXPRESSIONS)} 枚生成されました")
    print("※ キャラが固定されない場合は動画の失敗分析シーンを参照してください")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python generate_variants.py <avatar.png>")
        sys.exit(1)
    generate_variants(sys.argv[1])
