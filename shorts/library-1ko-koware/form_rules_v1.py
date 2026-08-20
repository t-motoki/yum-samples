"""更新前の共通入力チェック。"""


def validate_user_id(value: str) -> str | None:
    """空でなければユーザーIDとして受け入れる。"""
    if value.strip():
        return None
    return "ユーザーIDを入力してください"
