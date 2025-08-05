"""
Setup script for the Codegen SDK.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Read version from __init__.py
def get_version():
    init_path = os.path.join(os.path.dirname(__file__), "__init__.py")
    with open(init_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"

setup(
    name="codegen",
    version=get_version(),
    description="Python SDK to interact with Codegen SWE agents via API",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Codegen",
    author_email="support@codegen.com",
    url="https://github.com/codegen-sh/codegen-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
            "pre-commit>=2.0",
        ],
        "cli": [
            "click>=8.0",
            "rich>=10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "codegen=codegen.cli:main",
        ],
    },
    keywords=[
        "codegen",
        "ai",
        "software engineering",
        "automation",
        "api",
        "sdk",
        "agent",
        "development",
        "code review",
        "pull request",
    ],
    project_urls={
        "Documentation": "https://docs.codegen.com",
        "Source": "https://github.com/codegen-sh/codegen-sdk",
        "Tracker": "https://github.com/codegen-sh/codegen-sdk/issues",
        "Homepage": "https://codegen.com",
    },
)

