#!/bin/bash
# Builds "Desktop to Drive.app" from app.applescript (osacompile comes with macOS).
# Usage: mac/build-app.sh [output folder]   (default: /Applications)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-/Applications}/Desktop to Drive.app"
rm -rf "$OUT"
osacompile -o "$OUT" "$HERE/app.applescript"
# Use the macOS Desktop folder icon when available
ICON=/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/DesktopFolderIcon.icns
[ -f "$ICON" ] && cp "$ICON" "$OUT/Contents/Resources/applet.icns" && touch "$OUT"
echo "Built: $OUT"
