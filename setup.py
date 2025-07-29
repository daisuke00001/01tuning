#!/usr/bin/env python3
"""
Setup script for 01tuning project
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="01tuning",
    version="1.0.0",
    author="01tuning Team",
    author_email="",
    description="LLM Fine-tuning Project for TinySwallow and Patent Data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/daisuke00001/01tuning",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.42.1",
        "datasets>=2.14.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "PyYAML>=6.0",
        "tqdm>=4.64.0",
        "jupyter>=1.0.0",
        "notebook>=6.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "colab": [
            "unsloth[colab-new]>=2024.9",
            "bitsandbytes>=0.41.0",
            "accelerate>=0.21.0",
            "peft>=0.4.0",
            "trl>=0.7.0",
            "xformers>=0.0.29",
            "sentencepiece>=0.1.99",
            "protobuf>=3.20.0",
            "huggingface-hub>=0.16.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "01tuning-train=src.training_utils:main",
            "01tuning-eval=src.inference_utils:main",
            "01tuning-data=src.data_processing:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["configs/*.yaml", "data/samples/*"],
    },
)