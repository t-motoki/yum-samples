"""1行削除の前後を、元のサンプルを変えずに実行・記録する。"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


IMPORT_LINE = "from validation import validate\n"
PROCESS_FILE = "process_data.py"


def _run_process(directory: Path) -> dict[str, str | int]:
    result = subprocess.run(
        [sys.executable, PROCESS_FILE],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _remove_validate_import(process_path: Path) -> None:
    source = process_path.read_text(encoding="utf-8")
    if IMPORT_LINE not in source:
        raise ValueError("削除対象の validate import 行が見つかりません")
    process_path.write_text(source.replace(IMPORT_LINE, "", 1), encoding="utf-8")


def run_demo(source_dir: Path) -> dict[str, dict[str, str | int]]:
    """成功版とimport行削除版を別コピーで実行して結果を返す。"""
    with tempfile.TemporaryDirectory() as temporary_directory:
        work_dir = Path(temporary_directory) / "sample"
        shutil.copytree(source_dir, work_dir, ignore=shutil.ignore_patterns("__pycache__"))
        success = _run_process(work_dir)
        _remove_validate_import(work_dir / PROCESS_FILE)
        removed_import = _run_process(work_dir)
    return {"success": success, "removed_import": removed_import}


def write_demo_recording(source_dir: Path, output_path: Path) -> None:
    """実行結果を動画素材が読み取れるJSONとして保存する。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(run_demo(source_dir), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="1行削除の実行結果を記録します")
    parser.add_argument("--output", type=Path, required=True, help="記録JSONの出力先")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    write_demo_recording(Path(__file__).parent, arguments.output)
    print(f"記録を保存しました: {arguments.output}")
