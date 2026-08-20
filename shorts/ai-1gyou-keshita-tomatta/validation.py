"""処理対象の値がすべて正の整数かを検証する。"""


def validate(values: list[int]) -> bool:
    """正の整数だけで構成される入力を受け入れる。"""
    return all(isinstance(value, int) and value > 0 for value in values)
