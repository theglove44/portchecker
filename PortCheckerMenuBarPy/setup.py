from setuptools import setup

APP = ["portchecker_menu.py"]
DATA_FILES = []

OPTIONS = {
    "argv_emulation": False,
    "packages": ["portchecker"],
    "includes": [
        "portchecker.scanner",
        "portchecker.models",
        "portchecker.security",
        "portchecker.fingerprint",
        "portchecker.process_control",
        "portchecker.config",
    ],
    "plist": {
        "CFBundleName": "Port Checker",
        "CFBundleDisplayName": "Port Checker",
        "CFBundleIdentifier": "com.portchecker.menubar",
        "CFBundleShortVersionString": "1.0.0",
        "LSUIElement": True,
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
