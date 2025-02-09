#!/bin/bash

# Exit on any error
set -e

# Create log directory
LOG_DIR="/var/log/fileservice"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Set ownership
chown -R root:wheel "$LOG_DIR"

# Copy launchd plist
LAUNCHD_PLIST="/Library/LaunchDaemons/com.macos.fileservice.plist"
cp "/Applications/FileService.app/Contents/Resources/com.macos.fileservice.plist" "$LAUNCHD_PLIST"

# Set correct permissions for launchd plist
chown root:wheel "$LAUNCHD_PLIST"
chmod 644 "$LAUNCHD_PLIST"

# Load service
launchctl load "$LAUNCHD_PLIST"

echo "FileService installation completed successfully"
exit 0