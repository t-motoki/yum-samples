// シナリオ・スナップショットを workspace（作業ツリー）へ実体化する。
//
// なぜコピー方式か:
//   samples は公開リポジトリ yum-samples の git submodule であり、中にネスト git を作れない。
//   コピー方式なら submodule 制約と無関係に、何テイク録っても同一の初期状態へ機械的に戻せる。
//
// 物理隔離（設計 §3）:
//   workspace は apparatus の外（既定はリポジトリ外の絶対パス）に作る。装置（oracle/snapshot/
//   scripts/README/context）は workspace には一切コピーされない。AI が見るのは素のライブラリだけ。
//
// 決定性:
//   置換方式。node_modules を除く既存の中身を消してから snapshot を入れる（テイク中に AI が
//   足したファイルを次テイクに持ち越さない）。node_modules は温存し、無い時だけ npm ci する。
//   symlink は作らない（L4 遮断）。UI・日時・乱数・ネットワーク分岐なし（npm ci のみ外部）。
import {
  cpSync,
  rmSync,
  mkdirSync,
  existsSync,
  readdirSync,
  lstatSync,
} from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { resolveWorkspace, parseScenario } from "./workspace-path.mjs";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const apparatusRoot = dirname(scriptDir);

const argv = process.argv.slice(2);
const scenario = parseScenario(argv);
const workspace = resolveWorkspace(argv);

const snapshot = join(apparatusRoot, "scenarios", scenario, "snapshot");
if (!existsSync(snapshot)) {
  console.error(`エラー: シナリオ ${scenario} の snapshot が見つかりません: ${snapshot}`);
  process.exit(1);
}

// workspace を用意。既存なら node_modules 以外を消して決定的に置換する。
mkdirSync(workspace, { recursive: true });
for (const entry of readdirSync(workspace)) {
  if (entry === "node_modules") continue; // 温存（速度）。symlink でないことは後段で確認
  rmSync(join(workspace, entry), { recursive: true, force: true });
}

// snapshot の中身（src/tests/config/package.json/package-lock.json）を実体コピーする。
// snapshot に node_modules は無いので workspace の node_modules は保持される。
for (const entry of readdirSync(snapshot)) {
  cpSync(join(snapshot, entry), join(workspace, entry), {
    recursive: true,
    dereference: true, // 実体をコピー。万一 snapshot 側に symlink があっても実体化する
  });
}

// node_modules をローカル実体で用意する（symlink 禁止＝L4）。
const nodeModules = join(workspace, "node_modules");
if (!existsSync(nodeModules)) {
  console.log("[materialize] node_modules が無いため npm ci を実行します…");
  execFileSync("npm", ["ci"], { cwd: workspace, stdio: "inherit" });
} else if (lstatSync(nodeModules).isSymbolicLink()) {
  // 親経由で装置が露見するのを防ぐため、symlink の node_modules は許容しない。
  console.error("エラー: node_modules が symlink です。実体である必要があります（L4）。");
  process.exit(1);
}

console.log(`[materialize] シナリオ ${scenario} を ${workspace} へ実体化しました。`);
console.log(`  作業ツリー: ${workspace}`);
