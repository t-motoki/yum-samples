"""ログイン画面の最小再現。"""

from form_rules_v1 import validate_user_id


USER_ID = "yumu"


def main() -> int:
    error = validate_user_id(USER_ID)
    if error:
        print(f"ログイン失敗: {error}")
        return 1
    print(f"ログイン成功: {USER_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
