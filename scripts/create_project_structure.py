#!/usr/bin/env python3
"""
プロジェクト構造を自動作成するスクリプト
"""
import os

def create_directories():
    """必要なディレクトリを作成"""
    directories = [
        "notebooks",
        "src", 
        "configs",
        "data/raw",
        "data/processed", 
        "data/samples",
        "scripts",
        "tests",
        "docs",
        "models/saved_models",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}/")

def create_init_files():
    """__init__.pyファイルを作成"""
    init_files = ["src/__init__.py", "tests/__init__.py"]
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write('# This file makes Python treat the directory as a package\n')
        print(f"✅ Created: {init_file}")

if __name__ == "__main__":
    print("🏗️  プロジェクト構造を作成中...")
    create_directories()
    create_init_files()
    print("🎉 プロジェクト構造の作成完了！")