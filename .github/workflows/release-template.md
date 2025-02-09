# FileService Release ${version}

## Installation
1. Download `FileService.pkg`
2. Double-click to run the installer
3. Follow the installation prompts

## System Requirements
- macOS 10.15 or later
- Administrative privileges for installation

## Changes in this Release
${changes}

## Verification Steps
After installation:
1. Check service status:
   ```bash
   sudo launchctl list | grep fileservice
   ```
2. Check logs:
   ```bash
   tail -f /var/log/fileservice/fileservice.log
   ```

## Uninstallation
To uninstall:
1. Stop the service:
   ```bash
   sudo launchctl unload /Library/LaunchDaemons/com.yourcompany.fileservice.plist
   ```
2. Remove files:
   ```bash
   sudo rm -rf /Applications/FileService.app
   sudo rm /Library/LaunchDaemons/com.yourcompany.fileservice.plist
   sudo rm -rf /var/log/fileservice
   ```