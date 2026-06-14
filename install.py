#!/usr/bin/env python3
"""Bootstrap the local TriReason development environment."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / "venv"
FRONTEND_DIR = ROOT / "frontend"
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"


def print_step(message: str) -> None:
    print(f"\n==> {message}")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_command(command: list[str], *, cwd: Path | None = None) -> None:
    printable = " ".join(command)
    location = str(cwd or ROOT)
    print(f"[run] {printable} (cwd={location})")
    subprocess.run(command, cwd=cwd or ROOT, check=True)


def get_venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def find_npm() -> str:
    candidates = ["npm.cmd", "npm"] if os.name == "nt" else ["npm"]
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate
    fail("Node.js/NPM not found in PATH. Install Node.js 18+ and retry.")
    raise AssertionError("unreachable")


def ensure_python_version() -> None:
    version = sys.version_info
    if version < (3, 11):
        fail(
            "Python 3.11 or newer is required. "
            f"Current version: {version.major}.{version.minor}.{version.micro}"
        )


def create_virtualenv() -> Path:
    venv_python = get_venv_python()
    if venv_python.exists():
        print_step(f"Virtual environment already present at {VENV_DIR}")
        return venv_python

    print_step(f"Creating virtual environment at {VENV_DIR}")
    builder = venv.EnvBuilder(with_pip=True, clear=False, upgrade_deps=False)
    builder.create(VENV_DIR)

    if not venv_python.exists():
        fail("Virtual environment creation failed: Python executable not found inside venv.")
    return venv_python


def ensure_env_file() -> None:
    if ENV_FILE.exists():
        print_step(".env already present")
        return
    if not ENV_EXAMPLE.exists():
        fail("Missing .env.example template.")

    shutil.copy2(ENV_EXAMPLE, ENV_FILE)
    print_step("Created .env from .env.example")


def install_backend(venv_python: Path) -> None:
    print_step("Upgrading pip tooling inside the virtual environment")
    run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    print_step("Installing backend dependencies")
    run_command([str(venv_python), "-m", "pip", "install", "-e", ".[dev]"])


def install_frontend() -> None:
    npm = find_npm()
    if not FRONTEND_DIR.exists():
        fail("Frontend directory not found.")

    print_step("Installing frontend dependencies")
    run_command([npm, "install"], cwd=FRONTEND_DIR)


def main() -> None:
    ensure_python_version()
    print("TriReason installer")
    print(f"Project root: {ROOT}")
    print(f"Using Python: {sys.executable}")

    venv_python = create_virtualenv()
    ensure_env_file()
    install_backend(venv_python)
    install_frontend()

    print_step("Installation completed")
    print(f"Virtual environment Python: {venv_python}")
    print("Next step: run `python start.py`")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(f"Command failed with exit code {exc.returncode}")
