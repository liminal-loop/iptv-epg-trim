from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a self-contained executable with PyInstaller."
    )
    parser.add_argument(
        "--name",
        default="epg-trim",
        help="Output executable name (default: epg-trim)",
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Build as onedir instead of onefile",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Run PyInstaller with --clean",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    root = Path(__file__).resolve().parents[1]
    entrypoint = root / "src" / "epg_trim" / "main.py"

    target_dir = f"{platform.system().lower()}-{platform.machine().lower()}"
    dist_path = root / "dist" / target_dir
    build_path = root / "build" / target_dir

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        args.name,
        "--paths",
        str(root / "src"),
        "--distpath",
        str(dist_path),
        "--workpath",
        str(build_path),
        "--specpath",
        str(build_path),
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
    ]

    if args.onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    if args.clean:
        cmd.append("--clean")

    cmd.append(str(entrypoint))

    subprocess.run(cmd, cwd=root, check=True)


if __name__ == "__main__":
    main()
