#!/usr/bin/env python3
"""
クリーニング済みデータの確認スクリプト
"""

import json
import os
from pathlib import Path

def check_cleaned_data():
    """クリーニング済みデータの内容を確認"""
    
    data_dir = Path("data/cleaned")
    
    print("🔍 クリーニング済みデータチェック")
    print("=" * 50)
    
    # 各ファイルをチェック
    json_files = [
        "cleaned_patents_small.json",
        "cleaned_patents_medium.json", 
        "cleaned_training_dataset.json"
    ]
    
    for filename in json_files:
        filepath = data_dir / filename
        if not filepath.exists():
            print(f"❌ ファイルが存在しません: {filename}")
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n📊 {filename}:")
            print(f"  - データ数: {len(data):,}")
            
            if len(data) > 0:
                sample = data[0]
                print(f"  - キー: {list(sample.keys())}")
                
                if 'text' in sample:
                    text = sample['text']
                    print(f"  - テキスト長: {len(text):,}")
                    print(f"  - プレビュー: {text[:150]}...")
                    
                    # 異常文字列チェック
                    abnormal_patterns = ['CHEMICAL', 'LEGAL', 'MIC', 'CHCHCHCH']
                    found_patterns = [p for p in abnormal_patterns if p in text]
                    if found_patterns:
                        print(f"  - ⚠️ 残存異常パターン: {found_patterns}")
                    else:
                        print(f"  - ✅ クリーニング済み")
                
                # ファイルサイズ
                file_size = filepath.stat().st_size / (1024 * 1024)
                print(f"  - ファイルサイズ: {file_size:.2f} MB")
                
        except Exception as e:
            print(f"❌ {filename} 読み込みエラー: {e}")
    
    print(f"\n📋 Google Colabでの使用推奨:")
    print(f"  1. テスト用: cleaned_patents_small.json (50件)")
    print(f"  2. 中テスト用: cleaned_patents_medium.json (200件)")
    print(f"  3. 本格用: cleaned_training_dataset.json (436件)")
    
    # 統計情報を表示
    stats_file = data_dir / "cleaning_stats.json"
    if stats_file.exists():
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        print(f"\n📈 クリーニング統計:")
        for filename, stat in stats.items():
            if 'processing_summary' in stat:
                summary = stat['processing_summary']
                print(f"  {filename}:")
                print(f"    - 元データ: {summary['original_count']}件")
                print(f"    - クリーニング後: {summary['cleaned_count']}件")
                print(f"    - 保持率: {summary['retention_rate']:.1f}%")

if __name__ == "__main__":
    check_cleaned_data()