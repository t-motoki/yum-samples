// 作業ツリー（workspace）の実体化先パスを解決する共有ヘルパー。
//
// 物理隔離の要件（設計 §3）: workspace は apparatus の子ディレクトリにしない。
// AI が親を ls しても装置が見えない、リポジトリ外の innocent なパスを既定にする。
//
// 優先順位:
//   1. コマンドライン引数 --to <path>
//   2. 環境変数 EP70_WORKDIR
//   3. 既定 os.tmpdir()/kaikei（リポジトリ外の絶対パス）
import os from "node:os";
import { join, resolve } from "node:path";

export function resolveWorkspace(argv) {
  const i = argv.indexOf("--to");
  if (i !== -1 && argv[i + 1]) {
    return resolve(argv[i + 1]);
  }
  if (process.env.EP70_WORKDIR) {
    return resolve(process.env.EP70_WORKDIR);
  }
  return join(os.tmpdir(), "kaikei");
}

export function parseScenario(argv) {
  const i = argv.indexOf("--scenario");
  const value = i !== -1 ? argv[i + 1] : undefined;
  if (value !== "A" && value !== "B") {
    console.error("エラー: --scenario には A または B を指定してください。");
    process.exit(2);
  }
  return value;
}
