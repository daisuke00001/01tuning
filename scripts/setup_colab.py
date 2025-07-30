# Google Colab 用のセットアップスクリプト

import subprocess
import sys
import os

def install_colab_dependencies():
    """Colab用の依存関係をインストール"""
    print("Colab用の依存関係をインストール中...")

    # Colab環境の検出
    if "COLAB_GPU" in os.environ or "COLAB_" in ''.join(os.environ.keys()):
        print("Colab環境を検出しました。")

        # Unslothのインストール
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--no-deps",
            "bitsandbytes", "accelerate", "xformers==0.0.29.post3", 
            "peft", "trl", "triton", "cut_cross_entropy", "unsloth_zoo"
        ], check=True)

        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "sentencepiece", "protobuf", "datasets>=3.4.1,<4.0.0", 
            "huggingface_hub", "hf_transfer"
        ], check=True)

        subprocess.run([
                        sys.executable, "-m", "pip", "install", "--no-deps", "unsloth"
        ], check=True)

        # ライブラエラー対応
        print("ライブラリエラー対応...")
        subprocess.run([sys.executable, "-m", "pip", "install", "xformers"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "torchvision", "-y"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "torchvision", "--no-cache-dir"], check=True)

        print("✅ Colab環境セットアップ完了")
    else:
        print("Colab環境を検出しませんでした。")

def clone_repository(repo_url: str =  "https://github.com/daisuke00001/01tuning.git"):
    """リポジトリをクローン"""
    print("リポジトリをクローン中: {repo_url}")

    if os.path.exists("01tuning"):
        print("リポジトリは既に存在します。git pullで更新します。")
        subprocess.run(["git", "-C", "01tuning", "pull"], check=True)
    else:
        subprocess.run(["git", "clone", repo_url], check=True)

    os.chdir("01tuning")
    print("✅ リポジトリクローン完了")

if __name__ == "__main__":
    install_colab_dependencies()
    clone_repository()
    print("🎉 セットアップ完了")