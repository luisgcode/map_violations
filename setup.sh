#!/usr/bin/env bash
#!/usr/bin/env bash
# POSIX shell wrapper for bootstrap.py
# Usage: ./setup.sh  or  ./setup.sh --yes

set -e

if command -v python3 >/dev/null 2>&1; then
	PY=python3
elif command -v python >/dev/null 2>&1; then
	PY=python
else
	echo "python3 not found in PATH. Attempting to install..."
	if command -v apt-get >/dev/null 2>&1; then
		echo "Detected apt-get. Installing python3 and venv..."
		sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
	elif command -v dnf >/dev/null 2>&1; then
		echo "Detected dnf. Installing python3..."
		sudo dnf install -y python3 python3-venv python3-pip
	elif command -v pacman >/dev/null 2>&1; then
		echo "Detected pacman. Installing python..."
		sudo pacman -Syu --noconfirm python
	elif command -v brew >/dev/null 2>&1; then
		echo "Detected brew. Installing python..."
		brew install python
	else
		echo "Could not detect supported package manager. Please install Python 3.8+ and re-run." >&2
		exit 1
	fi
	if command -v python3 >/dev/null 2>&1; then
		PY=python3
	else
		echo "Python installation attempted but python3 still not found. Please install manually." >&2
		exit 1
	fi
fi

# Run bootstrap and auto-run the app after setup
${PY} bootstrap.py --venv .venv "$@" --run
