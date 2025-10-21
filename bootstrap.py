#!/usr/bin/env python3
"""
Bootstrap script for the MAP Violations project.

What it does:
- Ensures a Python >= 3.8 interpreter is available (the script is intended to be run with Python).
- Creates a virtual environment in `./.venv` (unless overridden).
- Upgrades pip inside the venv and installs packages from `requirements.txt`.
- Creates expected folders (`output`, `uploads`).
- Prints activation instructions for the current platform.

Usage:
    python bootstrap.py        # interactive flow
    python bootstrap.py --yes  # non-interactive, accept defaults
    python bootstrap.py --venv .venv

The wrapper scripts `setup.ps1` and `setup.sh` call this script for convenience.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

MIN_PY = (3, 8)

ROOT = Path(__file__).resolve().parent
REQ_FILE = ROOT / "requirements.txt"
DEFAULT_VENV = ROOT / ".venv"
FOLDERS = [ROOT / "output", ROOT / "uploads"]


def check_python_version() -> None:
    if sys.version_info < MIN_PY:
        print(f"ERROR: Python {MIN_PY[0]}.{MIN_PY[1]}+ is required. Detected: {sys.version}")
        sys.exit(1)


def run(cmd: list[str], **kwargs) -> None:
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, **kwargs)


def create_venv(venv_path: Path) -> None:
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return

    print(f"Creating virtual environment at {venv_path}...")
    run([sys.executable, "-m", "venv", str(venv_path)])


def get_pip_executable(venv_path: Path) -> Path:
    if platform.system() == "Windows":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
    return pip_path

def get_python_executable(venv_path: Path) -> Path:
    if platform.system() == "Windows":
        py = venv_path / "Scripts" / "python.exe"
    else:
        py = venv_path / "bin" / "python"
    return py


def install_requirements(venv_path: Path, requirements_file: Path) -> None:
    pip_exe = get_pip_executable(venv_path)
    if not pip_exe.exists():
        print("pip not found in venv, attempting to bootstrap pip...")
        run([sys.executable, "-m", "ensurepip", "--upgrade"])  # best-effort

    print("Upgrading pip in the virtual environment...")
    run([str(pip_exe), "install", "--upgrade", "pip"]) 

    if requirements_file.exists():
        print(f"Installing packages from {requirements_file}...")
        run([str(pip_exe), "install", "-r", str(requirements_file)])
    else:
        print(f"No requirements.txt found at {requirements_file}. Skipping package install.")


def create_folders() -> None:
    for f in FOLDERS:
        if not f.exists():
            print(f"Creating folder: {f}")
            f.mkdir(parents=True, exist_ok=True)
        else:
            print(f"Folder already exists: {f}")


def print_next_steps(venv_path: Path) -> None:
    print("\nBootstrap completed successfully. Next steps:")
    if platform.system() == "Windows":
        print(f"  PowerShell: .\\{venv_path.name}\\Scripts\\Activate.ps1")
        print(f"  cmd.exe: {venv_path.name}\\Scripts\\activate.bat")
    else:
        print(f"  source ./{venv_path.name}/bin/activate")

    print("Then run the app, for example:")
    print("  python app_flask.py")
    


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap this repository (venv + deps)")
    parser.add_argument("--venv", default=str(DEFAULT_VENV), help="Path to virtualenv directory (default: ./.venv)")
    parser.add_argument("--yes", "-y", action="store_true", help="Accept prompts non-interactively")
    parser.add_argument("--run", action="store_true", help="Run the Flask app after bootstrapping")
    args = parser.parse_args()

    check_python_version()

    venv_path = Path(args.venv).resolve()

    if not args.yes:
        print("This script will create a virtual environment and install python dependencies.")
        print(f"Virtualenv path: {venv_path}")
        if REQ_FILE.exists():
            print(f"Requirements file: {REQ_FILE}")
        else:
            print("Warning: requirements.txt not found; no packages will be installed.")
        resp = input("Proceed? [y/N]: ").strip().lower()
        if resp not in ("y", "yes"):
            print("Aborted by user.")
            sys.exit(0)

    create_venv(venv_path)
    install_requirements(venv_path, REQ_FILE)
    create_folders()
    
    # Optionally run the app if requested
    if args.run:
        print("Starting the application inside the virtual environment...")
        python_exe = get_python_executable(venv_path)
        if not python_exe.exists():
            print(f"Python executable not found in venv at {python_exe}")
            return
        try:
            run([str(python_exe), "app_flask.py"])
        except subprocess.CalledProcessError as e:
            print(f"Failed to start app: {e}")
    
    print_next_steps(venv_path)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(1)
