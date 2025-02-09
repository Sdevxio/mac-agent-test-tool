"""
Setup script for building macOS application bundle
"""
from setuptools import setup

APP = ['src/fileservice/server/main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'grpc',
        'fileservice',
    ],
    'includes': [
        'pathlib',
        'concurrent.futures',
    ],
    'plist': {
        'LSUIElement': True,  # Don't show in dock
        'LSBackgroundOnly': True,  # Background-only app
        'CFBundleName': 'FileService',
        'CFBundleDisplayName': 'File Service',
        'CFBundleIdentifier': 'com.macos.fileservice',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    }
}

setup(
    name='FileService',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'grpcio>=1.60.0',
    ],
)