#!/usr/bin/env python3
"""Entry point for PyInstaller build."""

import sys
import os

# PyInstaller extracts to a temp directory (MEI), and the portchecker
# package is at the root level there, not in src/
# Just need to ensure current dir is in path for frozen mode
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

from portchecker.cli import app

if __name__ == "__main__":
    app()
