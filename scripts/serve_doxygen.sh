#!/usr/bin/env bash
# WARNING: vibe coded. Works, but read with suspicion before extending.
#
# Serve generated Doxygen docs on http://localhost.
# Docs live in docs/html (scripts/run_doxygen.sh / Doxyfile_dev).
# Port override: PORT=9000 scripts/serve_doxygen.sh
set -euo pipefail

# Repo root, regardless of call site.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

HTML_DIR="$REPO_ROOT/docs/html"
PORT="${PORT:-8000}"

# Docs missing? Generate first.
if [ ! -f "$HTML_DIR/index.html" ]; then
	echo "==> docs/html/index.html absent; running scripts/run_doxygen.sh"
	"$SCRIPT_DIR/run_doxygen.sh"
fi

echo "==> Serving $HTML_DIR at http://localhost:$PORT/"
echo "==> Ctrl-C to stop"
exec python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$HTML_DIR"
