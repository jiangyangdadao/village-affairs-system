#!/bin/bash
set -e
cd "$(dirname "$0")"
APP="村务系统.app"
cp -R "$APP" /Applications/
PLIST="$HOME/Library/LaunchAgents/com.cunwu.plist"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.cunwu</string>
<key>ProgramArguments</key><array><string>/Applications/$APP/Contents/MacOS/村务系统</string></array>
<key>RunAtLoad</key><true/>
<key>WorkingDirectory</key><string>/Applications/$APP</string>
</dict></plist>
EOF
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "安装完成。首次打开若提示无法验证开发者，请右键 村务系统.app → 打开。"
echo "浏览器访问 http://127.0.0.1:8080"
