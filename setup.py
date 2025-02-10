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
        'google.protobuf',  # Include protobuf explicitly
        'fileservice',
    ],
    'includes': [
        'google',
        'google.protobuf',
        'grpc',
        'pathlib',
    ],
    'plist': {
        'LSUIElement': True,
        'LSBackgroundOnly': True,
        'CFBundleName': 'FileService',
        'CFBundleIdentifier': 'com.macos.fileservice',
        'CFBundleVersion': '1.0.0',
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
