#!/usr/bin/env python3
"""
特許データ処理実行スクリプト

使用例:
    python scripts/run_patent_processing.py single  # 単一ファイルテスト
    python scripts/run_patent_processing.py bulk    # 一括処理
    python scripts/run_patent_processing.py quick   # クイックテスト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.data_processing import DataProcessor
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """メイン実行関数"""
    # 引数取得
    mode = sys.argv[1] if len(sys.argv) > 1 else "single"
    
    # 設定読み込み
    config_path = project_root / "configs" / "patent_config.yaml"
    config = Config.load_from_yaml(str(config_path))
    
    # データプロセッサー初期化
    processor = DataProcessor(config)
    
    try:
        if mode == "single":
            logger.info("🔄 単一ファイルテストモード")
            dataset = processor.load_patent_dataset()
            
        elif mode == "bulk":
            logger.info("🔄 一括処理モード")
            dataset = processor.load_patent_dataset()
            
            # 学習用データセット作成
            training_dataset = processor.create_patent_training_dataset("chatml")
            
            # 出力ディレクトリ作成
            output_dir = project_root / "data" / "processed"
            output_dir.mkdir(exist_ok=True)
            
            # ファイル保存
            training_dataset.to_json(output_dir / "patent_training_chatml.json")
            logger.info(f"✅ データセット保存完了: {output_dir / 'patent_training_chatml.json'}")
            
        elif mode == "quick":
            logger.info("🔄 クイックテストモード")
            # ダミーデータでテスト
            dataset = processor.create_dummy_dataset(size=10)
            logger.info(f"テストデータセット作成完了 (サンプル数: {len(dataset)})")
            
        else:
            logger.error(f"❌ 不明なモード: {mode}")
            sys.exit(1)
            
        logger.info("🎉 処理完了")
        
    except Exception as e:
        logger.error(f"❌ エラー発生: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()