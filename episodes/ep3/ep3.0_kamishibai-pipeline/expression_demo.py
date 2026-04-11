"""
ep3.0 サンプル: <!-- expression: xxx --> ディレクティブのパース動作デモ

台本 Markdown に expression ディレクティブを書くと、
各文の avatar_expression が自動的に設定される様子を確認できます。

実行方法:
    python expression_demo.py
"""

import re
import sys


# --- 有効な表情セット ---
VALID_EXPRESSIONS = frozenset({
    "normal", "smile", "surprise", "chibi", "joy", "angry", "thinking"
})


def parse_script(markdown_text: str) -> list[dict]:
    """
    Markdown 台本を文単位のシーンリストに変換する（簡易版）。

    Returns:
        list of {"text": str, "expression": str}
    """
    scenes = []
    current_expression = "normal"  # デフォルト表情

    for line in markdown_text.splitlines():
        stripped = line.strip()

        # セクション区切りはスキップ
        if not stripped or stripped == "---":
            continue

        # <!-- expression: xxx --> ディレクティブ
        m = re.match(r"<!--\s*expression:\s*(\w+)\s*-->$", stripped)
        if m:
            value = m.group(1)
            if value == "reset":
                current_expression = "normal"
            elif value in VALID_EXPRESSIONS:
                current_expression = value
            else:
                print(
                    f"警告: 未知の表情 '{value}' が指定されました。"
                    f"有効な値: {sorted(VALID_EXPRESSIONS)}",
                    file=sys.stderr,
                )
            continue

        # 通常のナレーション行（句点で分割）
        for sentence in re.split(r"(?<=[。！？])", stripped):
            sentence = sentence.strip()
            if sentence:
                scenes.append({"text": sentence, "expression": current_expression})

    return scenes


def main():
    sample_script = """
今回は6種の表情が揃いました。

<!-- expression: joy -->
表情豊かな動画パイプライン、完成です！

<!-- expression: thinking -->
次はどんな演出ができるでしょうか。

<!-- expression: angry -->
課題がまだ残っています。

<!-- expression: reset -->
最終的にはデフォルトに戻ります。

<!-- expression: unknown_typo -->
タイポの場合は警告が出てデフォルトにフォールバックします。
"""

    scenes = parse_script(sample_script)

    print("=== パース結果 ===")
    for i, scene in enumerate(scenes):
        print(f"[{i:02d}] {scene['expression']:10s} | {scene['text']}")


if __name__ == "__main__":
    main()
