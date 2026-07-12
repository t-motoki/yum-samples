// 「本当の仕様（コンテキスト）」を workspace へ渡す。
//
// 設計 §7: 旧「テストを書き換えるな」という禁止令ではなく、どの期待値が要件で・どれが取り決めか＋
// その根拠を書いた SPEC を、アーク「本当の仕様を渡す」の瞬間に workspace へ配置する。
// materialize 直後の初期 workspace には存在せず（種漏れ回避）、この操作で初めて現れる。
import { cpSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { resolveWorkspace, parseScenario } from "./workspace-path.mjs";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const apparatusRoot = dirname(scriptDir);

const argv = process.argv.slice(2);
const scenario = parseScenario(argv);
const workspace = resolveWorkspace(argv);

if (!existsSync(workspace)) {
  console.error(`エラー: workspace が見つかりません: ${workspace}（先に materialize してください）`);
  process.exit(1);
}

const source = join(apparatusRoot, "scenarios", scenario, "context", "SPEC.md");
const dest = join(workspace, "SPEC.md");
cpSync(source, dest, { dereference: true });

console.log(`[apply:context] シナリオ ${scenario} の SPEC.md を ${dest} へ配置しました。`);
