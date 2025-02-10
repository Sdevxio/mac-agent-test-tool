"""
Setup script for building macOS application bundle
"""
from setuptools import setup, find_packages

APP = ['src/fileservice/server/main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'grpc',
        'fileservice',
        'google.protobuf',  # Ensure protobuf files are included
        'concurrent.futures',  # Thread pool
    ],
    'includes': [
        'pathlib',
        'os',
        'logging',
        'grpc',
        'grpc_tools',
        'google.protobuf',
    ],
    'plist': {
        'LSUIElement': True,
        'LSBackgroundOnly': True,
        'CFBundleName': 'FileService',
        'CFBundleDisplayName': 'File Service',
        'CFBundleIdentifier': 'com.macos.fileservice',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    }
}

setup(
    name='FileService',
    version='1.0.0',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'grpcio>=1.60.0',
        'grpcio-tools>=1.60.0',
        'grpcio-testing>=1.60.0',
        'watchdog>=3.0.0',
    ],
    python_requires='>=3.8',
)
