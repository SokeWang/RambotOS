#!/bin/bash

APP_NAME="Rambot"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}_${VERSION}.dmg"
APP_PATH="dist/${APP_NAME}.app"
TEMP_DMG="dist/temp.dmg"

echo "Creating DMG for ${APP_NAME}..."

# 1. Remove existing DMG if it exists
rm -f "dist/${DMG_NAME}"
rm -f "${TEMP_DMG}"

# 2. Create a temporary disk image
hdiutil create -size 500m -fs HFS+ -volname "${APP_NAME} Installer" "${TEMP_DMG}"

# 3. Mount the temporary image
MOUNT_DIR=$(hdiutil attach "${TEMP_DMG}" | grep -o '/Volumes/.*' | head -n 1)
echo "Mounted at: ${MOUNT_DIR}"

# 4. Copy the app bundle
cp -R "${APP_PATH}" "${MOUNT_DIR}/"

# 5. Create a symlink to Applications
ln -s /Applications "${MOUNT_DIR}/Applications"

# 6. Unmount
hdiutil detach "${MOUNT_DIR}"

# 7. Convert to compressed read-only DMG
hdiutil convert "${TEMP_DMG}" -format UDZO -o "dist/${DMG_NAME}"

# 8. Clean up
rm -f "${TEMP_DMG}"

echo "Done! DMG created at dist/${DMG_NAME}"
