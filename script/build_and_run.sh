#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-run}"
APP_NAME="PortChecker"
BUNDLE_ID="com.portchecker.menubar"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
APP_BUNDLE="$DIST_DIR/Port Checker.app"
APP_CONTENTS="$APP_BUNDLE/Contents"
APP_BINARY="$APP_CONTENTS/MacOS/$APP_NAME"

make -C "$ROOT_DIR" build-cli
mkdir -p "$ROOT_DIR/swift/PortCheckerMenuBar/Resources"
cp "$DIST_DIR/portchecker" "$ROOT_DIR/swift/PortCheckerMenuBar/Resources/portchecker"
chmod +x "$ROOT_DIR/swift/PortCheckerMenuBar/Resources/portchecker"

cd "$ROOT_DIR"
swift build
BUILD_BINARY="$(swift build --show-bin-path)/$APP_NAME"

rm -rf "$APP_BUNDLE"
mkdir -p "$APP_CONTENTS/MacOS" "$APP_CONTENTS/Resources"
cp "$BUILD_BINARY" "$APP_BINARY"
cp "$ROOT_DIR/script/PortChecker-Info.plist" "$APP_CONTENTS/Info.plist"
cp "$ROOT_DIR/swift/PortCheckerMenuBar/Resources/portchecker" "$APP_CONTENTS/Resources/portchecker"
chmod +x "$APP_BINARY" "$APP_CONTENTS/Resources/portchecker"
codesign --force --deep --sign - "$APP_BUNDLE" >/dev/null

open_app() {
  pkill -x "$APP_NAME" >/dev/null 2>&1 || true
  /usr/bin/open -n "$APP_BUNDLE"
}

case "$MODE" in
  --build|build)
    ;;
  run)
    open_app
    ;;
  --debug|debug)
    pkill -x "$APP_NAME" >/dev/null 2>&1 || true
    lldb -- "$APP_BINARY"
    ;;
  --logs|logs)
    open_app
    /usr/bin/log stream --info --style compact --predicate "process == \"$APP_NAME\""
    ;;
  --telemetry|telemetry)
    open_app
    /usr/bin/log stream --info --style compact --predicate "subsystem == \"$BUNDLE_ID\""
    ;;
  --verify|verify)
    open_app
    sleep 1
    pgrep -x "$APP_NAME" >/dev/null
    ;;
  *)
    echo "usage: $0 [run|--build|--debug|--logs|--telemetry|--verify]" >&2
    exit 2
    ;;
esac
