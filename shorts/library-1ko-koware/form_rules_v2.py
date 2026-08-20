"""更新後の共通入力チェック。"""


REQUIREMENT = "ユーザーIDは8文字以上にする"
STORY_REASON = "外部サービス連携ではIDは8文字以上必要"
INTENDED_SCOPE = "新規登録"
MINIMUM_USER_ID_LENGTH = 8


def validate_user_id(value: str) -> str | None:
    """更新で導入された最小文字数を、共通入力に適用する。"""
    normalized = value.strip()
    if not normalized:
        return "ユーザーIDを入力してください"
    if len(normalized) < MINIMUM_USER_ID_LENGTH:
        return f"ユーザーIDは{MINIMUM_USER_ID_LENGTH}文字以上必要です"
    return None
