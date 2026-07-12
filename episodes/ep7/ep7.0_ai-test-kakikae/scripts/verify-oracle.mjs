// 独立オラクル（held-out）を workspace の src に対して起動するディスパッチャ。
//
// 起動系統の隔離（設計 §8）: オラクルは apparatus 側にのみ存在し、workspace には materialize されない。
// このコマンド（apparatus の verify:oracle）からのみ、workspace の src/kaikei.js を対象に走る。
// AI に渡す検査群（test/lint/typecheck）には含めない。各テイク末に人間が回す。
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { existsSync } from "node:fs";
import { resolveWorkspace, parseScenario } from "./workspace-path.mjs";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const apparatusRoot = dirname(scriptDir);

const argv = process.argv.slice(2);
const scenario = parseScenario(argv);
const workspace = resolveWorkspace(argv);

const oracleRunner = join(apparatusRoot, "scenarios", scenario, "oracle", "verify-oracle.mjs");
if (!existsSync(join(workspace, "src", "kaikei.js"))) {
  console.error(`エラー: workspace に src/kaikei.js がありません: ${workspace}（先に materialize してください）`);
  process.exit(1);
}

try {
  execFileSync("node", [oracleRunner, "--workdir", workspace], { stdio: "inherit" });
} catch {
  // オラクルが仕様違反を検出したときは exit code をそのまま伝播させる。
  process.exit(1);
}
