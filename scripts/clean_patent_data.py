#!/usr/bin/env python3
"""
特許データクリーニングスクリプト
ローカル環境でデータの前処理を実行
"""

import json
import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatentDataCleaner:
    """特許データクリーニングクラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "processed"
        self.output_dir = self.project_root / "data" / "cleaned"
        
        # 出力ディレクトリを作成
        self.output_dir.mkdir(exist_ok=True)
        
    def clean_patent_text(self, text: str) -> str:
        """特許テキストのクリーニング"""
        if not isinstance(text, str):
            return ""
        
        logger.debug(f"クリーニング前の文字数: {len(text)}")
        
        # 異常な文字列パターンを除去
        patterns_to_remove = [
            r'CHEMICAL\d+',     # CHEMICAL6479等
            r'LEGAL\d+',        # LEGAL170等  
            r'MIC[A-Z]*',       # MICA等
            r'CH{2,}',          # CHCHCHCH等（2文字以上の連続）
            r'AL\d+',           # AL20等
            r'LE[A-Z]*',        # LECHEMICAL等
            r'ECH[A-Z]*',       # ECHEMICAL等
            r'[A-Z]{6,}',       # 6文字以上の連続大文字
            r'\d{5,}',          # 5桁以上の連続数字
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text)
        
        # 連続する同じ文字を除去（3文字以上）
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        # 複数の空白を単一に
        text = re.sub(r'\s+', ' ', text)
        
        # 制御文字を除去
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 行頭・行末の空白を除去
        text = text.strip()
        
        logger.debug(f"クリーニング後の文字数: {len(text)}")
        return text
        
    def limit_text_length(self, text: str, max_length: int = 1000) -> str:
        """テキスト長を制限"""
        if len(text) <= max_length:
            return text
            
        # 文の区切りで切る
        sentences = text.split('。')
        result = ""
        
        for sentence in sentences:
            potential_result = result + sentence + '。'
            if len(potential_result) <= max_length:
                result = potential_result
            else:
                break
                
        # 文での区切りで何も残らない場合は、強制的に切る
        if not result:
            result = text[:max_length] + "..."
            
        return result
        
    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """個別アイテムの処理"""
        if not isinstance(item, dict):
            return None
            
        cleaned_item = {}
        
        for key, value in item.items():
            if key == 'text' and isinstance(value, str):
                # メインテキストフィールドの処理
                cleaned_text = self.clean_patent_text(value)
                cleaned_text = self.limit_text_length(cleaned_text, 800)
                cleaned_item[key] = cleaned_text
                
            elif isinstance(value, str):
                # その他の文字列フィールドの軽度クリーニング
                cleaned_value = self.clean_patent_text(value)
                # 長すぎる場合は制限
                if len(cleaned_value) > 500:
                    cleaned_value = cleaned_value[:500] + "..."
                cleaned_item[key] = cleaned_value
                
            elif isinstance(value, list):
                # リスト（claims等）の処理
                cleaned_list = []
                for list_item in value:
                    if isinstance(list_item, str):
                        cleaned_list_item = self.clean_patent_text(list_item)
                        if len(cleaned_list_item) > 300:
                            cleaned_list_item = cleaned_list_item[:300] + "..."
                        cleaned_list.append(cleaned_list_item)
                    else:
                        cleaned_list.append(list_item)
                cleaned_item[key] = cleaned_list
                
            else:
                # その他のフィールドはそのまま
                cleaned_item[key] = value
        
        # 有効性チェック
        text_field = cleaned_item.get('text', '')
        if len(text_field) < 50:  # 最小長チェック
            return None
            
        return cleaned_item
        
    def load_and_clean_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """ファイルを読み込んでクリーニング"""
        logger.info(f"ファイル処理開始: {file_path}")
        
        try:
            # 複数のエンコーディングを試行
            encodings = ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis']
            data = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        data = json.load(f)
                    logger.info(f"エンコーディング成功: {encoding}")
                    break
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            
            if data is None:
                logger.error(f"ファイル読み込み失敗: {file_path}")
                return []
            
            # データ形式の正規化
            if not isinstance(data, list):
                data = [data]
                
            logger.info(f"読み込みデータ数: {len(data)}")
            
            # クリーニング処理
            cleaned_data = []
            for i, item in enumerate(data):
                try:
                    cleaned_item = self.process_item(item)
                    if cleaned_item:
                        cleaned_data.append(cleaned_item)
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"処理進捗: {i + 1}/{len(data)}")
                        
                except Exception as e:
                    logger.warning(f"アイテム {i} の処理でエラー: {e}")
                    continue
            
            logger.info(f"クリーニング完了: {len(cleaned_data)}/{len(data)} 件の有効データ")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"ファイル処理エラー: {e}")
            return []
    
    def save_cleaned_data(self, data: List[Dict[str, Any]], output_filename: str):
        """クリーニング済みデータを保存"""
        output_path = self.output_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存完了: {output_path}")
            logger.info(f"保存データ数: {len(data)}")
            
            # ファイルサイズ表示
            file_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"ファイルサイズ: {file_size:.2f} MB")
            
        except Exception as e:
            logger.error(f"保存エラー: {e}")
    
    def generate_statistics(self, original_data: List[Dict], cleaned_data: List[Dict]) -> Dict:
        """統計情報を生成"""
        stats = {
            "processing_summary": {
                "original_count": len(original_data),
                "cleaned_count": len(cleaned_data),
                "retention_rate": len(cleaned_data) / len(original_data) * 100 if original_data else 0
            },
            "text_length_stats": {
                "original_avg_length": 0,
                "cleaned_avg_length": 0,
                "max_length": 0,
                "min_length": float('inf')
            }
        }
        
        # テキスト長統計
        if original_data:
            original_lengths = [len(str(item.get('text', ''))) for item in original_data]
            stats["text_length_stats"]["original_avg_length"] = sum(original_lengths) / len(original_lengths)
        
        if cleaned_data:
            cleaned_lengths = [len(str(item.get('text', ''))) for item in cleaned_data]
            stats["text_length_stats"]["cleaned_avg_length"] = sum(cleaned_lengths) / len(cleaned_lengths)
            stats["text_length_stats"]["max_length"] = max(cleaned_lengths)
            stats["text_length_stats"]["min_length"] = min(cleaned_lengths)
        
        return stats
    
    def run_cleaning(self):
        """メインクリーニング処理"""
        logger.info("=" * 60)
        logger.info("特許データクリーニング開始")
        logger.info("=" * 60)
        
        # 利用可能なファイルを検索
        json_files = list(self.data_dir.glob("*.json"))
        
        if not json_files:
            logger.error(f"JSONファイルが見つかりません: {self.data_dir}")
            return
        
        logger.info(f"見つかったJSONファイル: {len(json_files)}")
        for file_path in json_files:
            logger.info(f"  - {file_path.name}")
        
        # 各ファイルを処理
        all_cleaned_data = []
        all_stats = {}
        
        for file_path in json_files:
            # 元データを保持（統計用）
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
                if not isinstance(original_data, list):
                    original_data = [original_data]
            except:
                original_data = []
            
            # クリーニング実行
            cleaned_data = self.load_and_clean_file(file_path)
            
            if cleaned_data:
                # ファイル別保存
                output_filename = f"cleaned_{file_path.name}"
                self.save_cleaned_data(cleaned_data, output_filename)
                
                # 統計生成
                stats = self.generate_statistics(original_data, cleaned_data)
                all_stats[file_path.name] = stats
                
                # 全体データに追加
                all_cleaned_data.extend(cleaned_data)
        
        # 統合データセット保存
        if all_cleaned_data:
            self.save_cleaned_data(all_cleaned_data, "cleaned_all_patents.json")
            
            # 学習用小データセット作成（最初の50件）
            small_dataset = all_cleaned_data[:50]
            self.save_cleaned_data(small_dataset, "cleaned_patents_small.json")
            
            # 中サイズデータセット（最初の200件）
            medium_dataset = all_cleaned_data[:200]
            self.save_cleaned_data(medium_dataset, "cleaned_patents_medium.json")
        
        # 統計情報を保存
        stats_path = self.output_dir / "cleaning_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(all_stats, f, ensure_ascii=False, indent=2)
        
        logger.info("=" * 60)
        logger.info("データクリーニング完了")
        logger.info(f"出力ディレクトリ: {self.output_dir}")
        logger.info(f"統合データ数: {len(all_cleaned_data)}")
        logger.info("=" * 60)
        
        # サマリー表示
        if all_cleaned_data:
            sample = all_cleaned_data[0]
            logger.info("📊 サンプルデータ:")
            logger.info(f"  キー: {list(sample.keys())}")
            if 'text' in sample:
                logger.info(f"  テキスト長: {len(sample['text'])}")
                logger.info(f"  テキストプレビュー: {sample['text'][:150]}...")


def main():
    """メイン実行関数"""
    cleaner = PatentDataCleaner()
    cleaner.run_cleaning()

if __name__ == "__main__":
    main()