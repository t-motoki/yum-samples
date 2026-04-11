"""
アバター画像の背景除去サンプル

動画: Pythonとフリーツールだけでアバターを無料で作る
https://www.youtube.com/@yum-channel  (チャンネルURLに置き換えてください)
"""

from pathlib import Path

from PIL import Image
from rembg import new_session, remove


def remove_background(input_path: str, output_path: str) -> None:
    session = new_session("isnet-anime")  # アニメ調イラストに特化したモデル

    img = Image.open(input_path)
    result = remove(img, session=session)
    result.save(output_path)

    print(f"完了: {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使い方: python remove_bg.py <画像ファイル>")
        print("例:     python remove_bg.py avatar.jpg")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = str(Path(input_path).stem) + "_nobg.png"
    remove_background(input_path, output_path)
