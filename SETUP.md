Setup and bootstrap instructions

This repo includes a small bootstrap helper to make it easy to prepare a development
environment on any machine with Python 3.8+ installed.

Files added:

- `bootstrap.py` - Main Python bootstrap script (creates virtualenv, installs requirements, creates folders).
- `setup.ps1` - PowerShell wrapper for Windows users.
- `setup.sh` - POSIX shell wrapper for macOS/Linux users.

Quick steps (Windows PowerShell):

1. Open PowerShell and navigate to the repo folder.
2. Run (interactive):

   .\setup.ps1

   or non-interactive (accept defaults):

   .\setup.ps1 -Yes

Note: `setup.ps1` now attempts a best-effort automatic install of Python using
`winget` or `choco` if `python` is not found on Windows. This requires admin rights
and may prompt for confirmation. If automatic install is not possible, you'll be
asked to install Python manually.

Quick steps (macOS / Linux):

1. Open a terminal and navigate to the repo folder.
2. Run (interactive):

   ./setup.sh

   or non-interactive:

   ./setup.sh --yes

Note: `setup.sh` will try common package managers (apt, dnf, pacman, brew) to
install Python3 if it's missing. This uses `sudo` on Linux and may prompt for
your password.

What the bootstrap does:

- Creates a virtual environment at `./.venv` unless it already exists.
- Upgrades pip inside the venv and installs packages from `requirements.txt`.
- Creates required folders: `output/` and `uploads/`.
- Prints instructions to activate the venv and run the app.
- Optionally runs the Flask app after setup when invoked via the wrappers (the
  wrappers call the bootstrap with `--run`). If you don't want the app to start
  automatically, run the bootstrap with `--venv .venv` only or remove `--run`.

If Python is not installed:

- Install Python 3.8+ from https://www.python.org/downloads/
- On Windows select the "Add Python to PATH" option during install (or manually add it to PATH).

If you want the script to also install system-level packages (e.g. on Ubuntu), run:

    # Ubuntu example, only if required
    sudo apt update && sudo apt install -y python3-venv python3-pip

If you need any customization (different venv path, extra packages, or installing node/npm), tell me and I can extend the bootstrap.
