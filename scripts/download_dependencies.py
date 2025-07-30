"""
依存関係ダウンロードスクリプト
ローカル環境とGoogle Colab環境を自動検出、適切な依存関係をインストール
"""

import os
import sys
import subprocess
import platform
import importlib.util
from typing import List, Dict, Optional
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DependencyManager:
    """依存関係管理クラス"""
    
    def __init__(self):
        self.is_colab = self._detect_colab()
        self.is_cuda_available = self._check_cuda()
        self.python_version = self._get_python_version()
        self.platform_info = self._get_platform_info()
        
    def _detect_colab(self) -> bool:
        """Google Colab環境かどうかを検出"""
        colab_indicators = [
            'COLAB_GPU' in os.environ,
            'COLAB_TPU_ADDR' in os.environ,
             'COLAB_' in ''.join(os.environ.keys()),
             os.path.exists('/content'),
             os.path.exists('/opt/bin/nvidia-smi')
        ]
        return any(colab_indicators)
    
    def _check_cuda(self) -> bool:
        """CUDAの利用可能性を確認"""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
        
    def _get_python_version(self) -> str:
        """Pythonバージョンを取得"""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _get_platform_info(self) -> str:
        """プラットフォーム情報を取得"""
        return {
            'sysytem': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': self.python_version,
        }
        
    def _run_pip_command(self, args: List[str], check: bool = True) -> bool:
        """pipコマンドを実行"""
        try:
            cmd = [sys.executable, '-m', 'pip'] + args
            logger.info(f"実行中: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=check, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"コマンド失敗: {' '.join(cmd)}")
                logger.error(f"エラー出力: {result.stderr}")
                return False
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"pip コマンドエラー： {e}")
            return False
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            return False
        
    def install_base_dependencies(self) -> bool:
        """基本依存関係をインストール"""
        logger.info("📦 基本依存関係をインストール中...")
        
        base_packages = [
            'torch>=2.0.0',
            'transformers>=4.42.1',
            'datasets>=2.14.0',
            'numpy>=1.21.0',
            'pandas>=1.3.0',
            'PyYAML>=6.0',
            'tqdm>=4.64.0'
        ]
        
        success = True
        for package in base_packages:
            if not self._run_pip_command(['install', package]):
                success = False
                logger.error(f"✖ {package} のインストールに失敗")
            else:
                logger.info(f"✅ {package} のインストールに成功")
                
        return success
    
    def install_colab_dependencies(self) -> bool:
        """Google Colab環境の依存関係をインストール"""
        logger.info("📦 Google Colab環境の依存関係をインストール中...")
        
        # Unsloth関連のインストール
        unsloth_packages = [
            '--no-deps', 'bitsandbytes', 'accelerate', 'xformers==0.0.29.post3',
            'peft', 'trl', 'triton', 'cut_cross_entropy', 'unsloth_zoo'
        ]
        
        success = True
        
        # Unsloth依存関係
        if not self._run_pip_command(['install'] + unsloth_packages):
            success = False
            logger.error("❌ Unsloth関連の依存関係のインストールに失敗")
            
        # 追加パッケージ
        additional_packages = [
            'sentencepiece', 'protobuf', 'datasets>=3.4.1,<4.0.0',
            'huggingface_hub', 'hf_transfer'
        ]
        
        if not self._run_pip_command(['install'] + additional_packages):
            success = False
            logger.error("❌ 追加パッケージのインストールに失敗")
        
        if not self._run_pip_command(['install', '--no-deps', 'unsloth']):
            success = False
            logger.error("❌ Unsloth本体のインストールに失敗")
        
        return success
    
    def fix_library_conflicts(self) -> bool:
        """ライブラリコンフリクトを修正"""
        logger.info("🔧 ライブラリコンフリクトを修正中...")
        
        success = True
        
        # xformersの修正
        if not self._run_pip_command(['install', 'xformers', '--force-reinstall']):
            success = False
            logger.error("❌ xformers の修正に失敗")
        
        # torchvision の修正
        if not self._run_pip_command(['uninstall', 'torchvision', '-y'], check=False):
            logger.warning("⚠️  torchvision のアンインストールに失敗（元々なかった可能性）")
        
        if not self._run_pip_command(['install', 'torchvision', '--no-cache-dir']):
            success = False
            logger.error("❌ torchvision の再インストールに失敗")
        
        return success
    
    def install_development_dependencies(self) -> bool:
        """開発用依存関係をインストール"""
        logger.info("🚀 開発用依存関係をインストール中...")
        
        dev_packages = [
            'jupyter>=1.0.0',
            'notebook>=6.4.0',
            'pytest>=7.0.0',
            'black>=22.0.0',
            'flake8>=5.0.0',
            'mypy>=0.991'
        ]
        
        success = True
        for package in dev_packages:
            if not self._run_pip_command(['install', package]):
                success = False
                logger.error(f"❌ {package} のインストールに失敗")
        
        return success
 
    def verify_installation(self) -> Dict[str, bool]:
        """インストール状況を確認"""
        logger.info("🔍 インストール状況を確認中...")
        
        critical_packages = {
            'torch': 'torch',
            'transformers': 'transformers',
            'datasets': 'datasets',
            'yaml': 'PyYAML',
            'numpy': 'numpy',
            'pandas': 'pandas'
        }
        
        if self.is_colab:
            critical_packages.update({
                'unsloth': 'unsloth',
                'peft': 'peft',
                'trl': 'trl',
                'bitsandbytes': 'bitsandbytes'
            })
        
        results = {}
        for import_name, package_name in critical_packages.items():
            try:
                importlib.import_module(import_name)
                results[package_name] = True
                logger.info(f"✅ {package_name} インポート成功")
            except ImportError:
                results[package_name] = False
                logger.error(f"❌ {package_name} インポート失敗")
        
        return results
  
    def print_environment_info(self):
        """環境情報を表示"""
        print("\n" + "="*50)
        print("🖥️  環境情報")
        print("="*50)
        print(f"Python バージョン: {self.python_version}")
        print(f"プラットフォーム: {self.platform_info['system']} {self.platform_info['machine']}")
        print(f"Google Colab: {'✅ Yes' if self.is_colab else '❌ No'}")
        print(f"CUDA 利用可能: {'✅ Yes' if self.is_cuda_available else '❌ No'}")
        
        if self.is_cuda_available:
            try:
                import torch
                if torch.cuda.is_available():
                    print(f"PyTorch CUDA: ✅ {torch.version.cuda}")
                    print(f"GPU デバイス数: {torch.cuda.device_count()}")
                    if torch.cuda.device_count() > 0:
                        gpu_name = torch.cuda.get_device_name(0)
                        print(f"GPU 名: {gpu_name}")
            except ImportError:
                print("PyTorch CUDA: ❓ PyTorch not installed")
    
    def run_full_setup(self) -> bool:
        """完全なセットアップを実行"""
        logger.info("🚀 完全セットアップを開始...")
        
        self.print_environment_info()
        
        success = True
        
        # 1. 基本依存関係
        if not self.install_base_dependencies():
            success = False
        
        # 2. Colab専用依存関係（Colab環境の場合）
        if self.is_colab:
            if not self.install_colab_dependencies():
                success = False
            
            # 3. ライブラリコンフリクト修正
            if not self.fix_library_conflicts():
                success = False
        else:
            # ローカル環境の場合は開発用依存関係もインストール
            if not self.install_development_dependencies():
                success = False
        
        # 4. インストール確認
        verification_results = self.verify_installation()
        failed_packages = [pkg for pkg, status in verification_results.items() if not status]
        
        if failed_packages:
            success = False
            logger.error(f"❌ 以下のパッケージのインストール/インポートに失敗: {', '.join(failed_packages)}")
        
        # 結果サマリー
        print("\n" + "="*50)
        if success:
            print("🎉 セットアップ完了！")
        else:
            print("⚠️  セットアップ中にエラーが発生しました")
        print("="*50)
        
        return success

def main():
    """メイン実行関数"""
    print("🔧 TinySwallow LoRAチューニング - 依存関係セットアップ")
    print("="*60)
    
    manager = DependencyManager()
    success = manager.run_full_setup()
    
    if not success:
        print("\n❌ セットアップに失敗しました。ログを確認してください。")
        sys.exit(1)
    
    print("\n✅ 依存関係のセットアップが完了しました！")
    print("📝 次のステップ: python scripts/prepare_data.py でデータを準備してください")

if __name__ == "__main__":
    main()