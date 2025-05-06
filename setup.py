from setuptools import setup, find_packages

setup(
    name="pr_static_analysis",
    version="0.1.0",
    description="Static analysis system for GitHub pull requests",
    author="Codegen",
    author_email="codegen@example.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.2",
        "PyGithub>=1.55",
        "GitPython>=3.1.24",
    ],
    python_requires=">=3.8",
)

