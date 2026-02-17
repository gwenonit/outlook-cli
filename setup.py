from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="outlook-cli",
    version="0.1.0",
    author="Gwen",
    author_email="gwenonit@outlook.com",
    description="CLI wrapper for Microsoft Graph API - Outlook email, calendar, and tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gwenonit/outlook-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "requests>=2.25",
    ],
    extras_require={
        "keyring": ["keyring>=23.0"],
    },
    entry_points={
        "console_scripts": [
            "outlook=outlook_cli.main:cli",
        ],
    },
)
