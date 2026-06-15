#!/usr/bin/env bash
# Daily deploy: place today's brief, rebuild data + portal, commit, push.
# Usage: tools/deploy.sh <YYYY-MM-DD> <path-to-generated-brief.html>
set -euo pipefail
DATE="$1"; SRC="$2"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
git pull -q --rebase || true
python3 tools/add_brief.py "$DATE" "$SRC"
python3 tools/build.py
git add -A
git commit -q -m "Brief $DATE: archive + portal rebuild" || { echo "nothing to commit"; exit 0; }
git push -q origin main
echo "Deployed brief $DATE and rebuilt portal."
