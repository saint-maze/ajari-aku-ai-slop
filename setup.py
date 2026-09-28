from setuptools import setup, find_packages

setup(
    name="sysmon-cli",
    version="0.1.0",
    description="Cross-platform Python CLI system monitor and developer tool",
    packages=find_packages(include=["sysmon_cli", "sysmon_cli.*"], exclude=["tests*", "sysmon_cli.tests*"]),
    install_requires=[
        "psutil>=5.9.0",
    ],
    extras_require={
        "test": ["pytest>=7.0.0"],
    },
    entry_points={
        "console_scripts": [
            "sysmon=sysmon_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
)
