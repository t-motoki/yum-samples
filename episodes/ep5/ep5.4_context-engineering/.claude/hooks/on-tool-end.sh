#!/bin/bash
# PostToolUse hook のサンプル
# セッション終了コマンドが実行されたときに状態ファイルを更新する

# ツール入力にセッション終了コマンドが含まれるか確認
if echo "${CLAUDE_TOOL_INPUT_COMMAND:-}" | grep -q "session-end"; then
  echo "$(date '+%Y-%m-%d %H:%M'): セッション終了" >> tasks/session_log.txt
fi
