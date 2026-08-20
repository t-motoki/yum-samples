"""検証してから数値データを処理する最小サンプル。"""

from validation import validate


def process_data(values: list[int]) -> int:
    """検証済みの値を合計する。"""
    if not validate(values):
        raise ValueError("正の整数だけを指定してください")
    return sum(values)


if __name__ == "__main__":
    result = process_data([3, 5, 8])
    print(f"処理完了: 3件 / 合計: {result}")
