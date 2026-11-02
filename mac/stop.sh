#!/bin/bash
# Turns off automatic moving completely. A manual "Move now" still works.
DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL=com.desktop-to-drive
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
touch "$DIR/PAUSE"
echo "Desktop to Drive is OFF"
