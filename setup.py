from setuptools import setup, find_packages

setup(
    name="portfolio-rebalancer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests==2.31.0",
        "pyyaml==6.0.1",
        "gate_api==6.94.2",
    ],
    entry_points={
        'console_scripts': [
            'rebalancer=backend.main:main',
        ],
    },
) 