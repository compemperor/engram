"""
Engram setup for pip installation
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="engram",
    version="0.1.0",
    author="compemperor, Clawdy",
    author_email="your-email@example.com",  # TODO: Add real email
    description="Memory traces for AI agents - Self-improving memory system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/compemperor/engram",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "engram=engram.__main__:cli",
        ],
    },
)
