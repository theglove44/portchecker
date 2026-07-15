#!/bin/bash
# Build script for Port Checker
# Creates both CLI and Menu Bar app with bundled CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Port Checker...${NC}"

# Create directories
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

# Step 1: Build CLI
echo -e "\n${YELLOW}Step 1: Building CLI...${NC}"

cd "$PROJECT_ROOT"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
pip install -q -e ".[dev]"
pip install -q pyinstaller

# Build standalone binary
pyinstaller \
    --onefile \
    --name portchecker \
    --distpath "$DIST_DIR" \
    --specpath "$BUILD_DIR" \
    --workpath "$BUILD_DIR" \
    --clean \
    src/portchecker/__main__.py

echo -e "${GREEN}✓ CLI built at: $DIST_DIR/portchecker${NC}"

# Step 2: Setup Swift app resources
echo -e "\n${YELLOW}Step 2: Setting up Swift app...${NC}"

SWIFT_DIR="$PROJECT_ROOT/swift/PortCheckerMenuBar"
RESOURCES_DIR="$SWIFT_DIR/Resources"

mkdir -p "$RESOURCES_DIR"
cp "$DIST_DIR/portchecker" "$RESOURCES_DIR/"
chmod +x "$RESOURCES_DIR/portchecker"

echo -e "${GREEN}✓ CLI copied to app resources${NC}"

# Step 3: Build native SwiftUI app
echo -e "\n${YELLOW}Step 3: Building native SwiftUI menu bar app...${NC}"
cd "$PROJECT_ROOT"
./script/build_and_run.sh --build
echo -e "${GREEN}✓ Native app built at: $DIST_DIR/Port Checker.app${NC}"

# Step 4: Build Python menu bar app (fallback)
echo -e "\n${YELLOW}Step 4: Building Python menu bar app (fallback)...${NC}"

cd "$PROJECT_ROOT/PortCheckerMenuBarPy"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# Update setup.py to bundle CLI
python setup.py py2app

if [ -d "dist/Port Checker.app" ]; then
    cp -R "dist/Port Checker.app" "$DIST_DIR/Port Checker (Python).app"
    echo -e "${GREEN}✓ Python menu bar app built at: $DIST_DIR/Port Checker (Python).app${NC}"
fi

# Step 5: Create DMG
echo -e "\n${YELLOW}Step 5: Creating distribution package...${NC}"

cd "$DIST_DIR"

# Create a zip of the CLI
zip -q "portchecker-cli-macos.zip" portchecker

# Create app zip
if [ -d "Port Checker.app" ]; then
    zip -qry "Port-Checker.app.zip" "Port Checker.app"
fi

echo -e "${GREEN}✓ Distribution packages created${NC}"

# Summary
echo -e "\n${GREEN}Build complete!${NC}"
echo ""
echo "Outputs:"
echo "  CLI:       $DIST_DIR/portchecker"
echo "  CLI Zip:   $DIST_DIR/portchecker-cli-macos.zip"
if [ -d "$DIST_DIR/Port Checker.app" ]; then
    echo "  App:       $DIST_DIR/Port Checker.app"
fi
if [ -d "$DIST_DIR/Port Checker (Python).app" ]; then
    echo "  Py App:    $DIST_DIR/Port Checker (Python).app"
fi

echo ""
echo "Install:"
echo "  CLI:  cp $DIST_DIR/portchecker /usr/local/bin/"
echo "  App:  cp -R '$DIST_DIR/Port Checker.app' /Applications/"
