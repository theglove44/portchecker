from setuptools import setup

APP = ["portchecker_menu.py"]
DATA_FILES = []

OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "Port Checker",
        "CFBundleDisplayName": "Port Checker",
        "CFBundleIdentifier": "com.portchecker.menubar",
        "LSUIElement": True,
        "CFBundleShortVersionString": "1.0.0",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
