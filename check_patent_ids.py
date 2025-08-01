#!/usr/bin/env python3
"""
patent_idの問題を調査するスクリプト
"""

import json
from pathlib import Path
from collections import Counter

def check_patent_ids():
    """patent_idの状況を詳しく調査"""
    
    print("🔍 Patent ID問題の調査")
    print("=" * 50)
    
    # 元データを確認
    data_path = Path("data/cleaned/cleaned_patents_medium.json")
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 総データ数: {len(data)}")
    
    # patent_idの分布を確認
    patent_ids = []
    for item in data:
        pid = item.get('patent_id', 'MISSING_KEY')
        if pid is None:
            pid = 'NULL_VALUE'
        elif pid == '':
            pid = 'EMPTY_STRING'
        patent_ids.append(pid)
    
    # 頻度を確認
    id_counter = Counter(patent_ids)
    print(f"\n📋 Patent ID分布:")
    for pid, count in id_counter.most_common(10):
        print(f"  '{pid}': {count}件")
    
    # サンプルデータの詳細確認
    print(f"\n🔍 最初の5件の詳細:")
    for i, item in enumerate(data[:5]):
        print(f"\n{i+1}件目:")
        print(f"  patent_id: '{item.get('patent_id', 'MISSING')}'")
        print(f"  section: '{item.get('section', 'MISSING')}'")
        print(f"  text: '{item.get('text', 'MISSING')[:50]}...'")
    
    # 問題の分析
    unique_ids = set(patent_ids)
    print(f"\n📈 統計:")
    print(f"  - ユニークpatent_id数: {len(unique_ids)}")
    print(f"  - 総データ数: {len(data)}")
    print(f"  - 平均セクション数/特許: {len(data) / len(unique_ids):.1f}")
    
    if len(unique_ids) == 1:
        print(f"  ⚠️ 全てのデータが同じpatent_idを持っています: '{list(unique_ids)[0]}'")
        return False
    elif len(unique_ids) < 10:
        print(f"  ⚠️ patent_idの種類が少なすぎます")
        return False
    else:
        print(f"  ✅ patent_IDは正常に分散しています")
        return True

def investigate_original_data():
    """元のクリーニング前データも確認"""
    
    print(f"\n" + "=" * 50)
    print("🔍 元データ（sections_dataset）の調査")
    
    sections_path = Path("data/cleaned/cleaned_sections_dataset.json")
    if not sections_path.exists():
        print("❌ sections_datasetが見つかりません")
        return
    
    with open(sections_path, 'r', encoding='utf-8') as f:
        sections_data = json.load(f)
    
    print(f"📊 Sectionsデータ数: {len(sections_data)}")
    
    # patent_idの分布
    section_patent_ids = [item.get('patent_id', 'MISSING') for item in sections_data]
    section_id_counter = Counter(section_patent_ids)
    
    print(f"📋 Sections Patent ID分布 (上位10件):")
    for pid, count in section_id_counter.most_common(10):
        print(f"  '{pid}': {count}件")
    
    # 比較
    unique_section_ids = set(section_patent_ids)
    print(f"\n📈 Sections統計:")
    print(f"  - ユニークpatent_id数: {len(unique_section_ids)}")
    print(f"  - 総データ数: {len(sections_data)}")
    print(f"  - 平均セクション数/特許: {len(sections_data) / len(unique_section_ids):.1f}")

if __name__ == "__main__":
    # patent_id問題の調査
    is_normal = check_patent_ids()
    
    # 元データの調査
    investigate_original_data()
    
    if not is_normal:
        print(f"\n🚨 根本原因:")
        print(f"  XMLファイルからの抽出時にpatent_idが正しく設定されていない")
        print(f"  → src/patent_processing/text_processor.py の修正が必要")