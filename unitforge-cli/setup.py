from setuptools import setup, find_packages

setup(
    name="unitforge",
    version="0.5.0",
    description="AI-powered unit test generation engine",
    author="Akshat",
    packages=find_packages(),
    install_requires=[
        "click==8.1.7",
        "requests==2.32.0",
        "rich==13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "unitforge=unitforge_cli.main:cli",
        ],
    },
    python_requires=">=3.12",
)
