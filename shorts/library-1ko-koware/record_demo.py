"""更新前後のログイン結果を、公開ソースを変えずに記録する。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEMO_DIR = Path(__file__).resolve().parent


def run_login(directory: Path) -> dict[str, int | str]:
    result = subprocess.run(
        [sys.executable, "login.py"],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )
    return {"returncode": result.returncode, "stdout": result.stdout}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="library-upgrade-demo-") as temp_dir:
        work_dir = Path(temp_dir) / "demo"
        shutil.copytree(DEMO_DIR, work_dir)
        before_upgrade = run_login(work_dir)

        login_path = work_dir / "login.py"
        login_path.write_text(
            login_path.read_text(encoding="utf-8").replace(
                "from form_rules_v1 import validate_user_id",
                "from form_rules_v2 import validate_user_id",
            ),
            encoding="utf-8",
        )
        after_upgrade = run_login(work_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"before_upgrade": before_upgrade, "after_upgrade": after_upgrade},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
