#!/bin/bash
# Turns on automatic moving: runs move.py every hour (and once now) with launchd.
DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL=com.desktop-to-drive
P="$HOME/Library/LaunchAgents/$LABEL.plist"
# The real python binary: this is the one that needs Full Disk Access (see README).
PY="$(/usr/bin/python3 -c 'import os, sys; print(os.path.realpath(sys.executable))')" || exit 1

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$P" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$PY</string><string>$DIR/move.py</string></array>
  <key>StartInterval</key><integer>3600</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>$DIR/errors.txt</string>
</dict></plist>
PLIST
rm -f "$DIR/PAUSE"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
launchctl bootstrap "gui/$(id -u)" "$P" && echo "Desktop to Drive is ON"
