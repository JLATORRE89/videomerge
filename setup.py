#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="mp3_mkv_merger",
    version="1.0.0",
    description="Combine MP3 audio files with MKV video files from OBS Studio",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "ffmpeg-python",
        "flask",
        "tqdm",
        "watchdog",
    ],
    entry_points={
        'console_scripts': [
            'mp3-mkv-merger=mp3_mkv_merger.main:main',
        ],
    },
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
