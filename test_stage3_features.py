#!/usr/bin/env python3
"""段階3: 文字数制限とセクション選択機能のテスト"""

import xml.etree.ElementTree as ET
from pathlib import Path

# 名前空間定義
namespaces = {
    'jppat': 'http://www.jpo.go.jp/standards/XMLSchema/ST96/JPPatent',
    'jpcom': 'http://www.jpo.go.jp/standards/XMLSchema/ST96/JPCommon',
    'com': 'http://www.wipo.int/standards/XMLSchema/ST96/Common',
    'pat': 'http://www.wipo.int/standards/XMLSchema/ST96/Patent'
}

def clean_xml_text(text):
    """XMLテキストのクリーニング"""
    import re
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'<com:Br\s*/>', '\n', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_with_config(root, sources, max_length):
    """設定可能な抽出処理をシミュレート"""
    tag_mapping = {
        'EmbodimentDescription': './/pat:EmbodimentDescription',
        'DetailedDescription': './/pat:DetailedDescription',
        'BestMode': './/pat:BestMode',
        'InventionMode': './/jppat:InventionMode'
    }
    
    for source in sources:
        if source not in tag_mapping:
            continue
            
        xpath = tag_mapping[source]
        elem = root.find(xpath, namespaces)
        
        if elem is not None:
            text = ET.tostring(elem, encoding='unicode', method='text')
            cleaned_text = clean_xml_text(text)
            
            if cleaned_text:
                original_length = len(cleaned_text)
                
                # 文字数制限の適用
                if len(cleaned_text) > max_length:
                    cleaned_text = cleaned_text[:max_length - 3] + "..."
                
                return source, original_length, len(cleaned_text), cleaned_text
    
    return None, 0, 0, ""

# テストケース
test_cases = [
    {
        'name': 'デフォルト設定（全タグ、50000文字制限）',
        'sources': ['EmbodimentDescription', 'DetailedDescription', 'BestMode', 'InventionMode'],
        'max_length': 50000
    },
    {
        'name': '従来設定（EmbodimentDescriptionとDetailedDescriptionのみ）',
        'sources': ['EmbodimentDescription', 'DetailedDescription'],
        'max_length': 50000
    },
    {
        'name': '文字数制限10000文字',
        'sources': ['EmbodimentDescription', 'DetailedDescription', 'BestMode', 'InventionMode'],
        'max_length': 10000
    },
    {
        'name': 'BestModeとInventionModeのみ',
        'sources': ['BestMode', 'InventionMode'],
        'max_length': 50000
    }
]

# 長文を含むファイルでテスト（0007624240.xml: InventionModeが16,183文字）
test_file = "/mnt/d/20250728/01tuning/data/JPB_2025018_0130発行分/DOCUMENT/P_B1/0007624201/0007624231/0007624240/0007624240.xml"

print("段階3: 文字数制限とセクション選択機能のテスト")
print("=" * 100)
print(f"テストファイル: {Path(test_file).name}")

try:
    tree = ET.parse(test_file)
    root = tree.getroot()
    
    # 特許番号
    patent_number_elem = root.find('.//pat:PublicationNumber', namespaces)
    patent_number = patent_number_elem.text if patent_number_elem is not None else "N/A"
    print(f"特許番号: {patent_number}\n")
    
    # 各タグの実際の文字数を確認
    print("【各タグの文字数】")
    tag_mapping = {
        'EmbodimentDescription': './/pat:EmbodimentDescription',
        'DetailedDescription': './/pat:DetailedDescription',
        'BestMode': './/pat:BestMode',
        'InventionMode': './/jppat:InventionMode'
    }
    
    for tag_name, xpath in tag_mapping.items():
        elem = root.find(xpath, namespaces)
        if elem is not None:
            text = ET.tostring(elem, encoding='unicode', method='text')
            text_length = len(clean_xml_text(text))
            print(f"  {tag_name}: {text_length:,}文字")
        else:
            print(f"  {tag_name}: なし")
    
    print("\n" + "-" * 100)
    
    # 各テストケースを実行
    for test_case in test_cases:
        print(f"\n【{test_case['name']}】")
        source, original_length, final_length, text = extract_with_config(
            root, test_case['sources'], test_case['max_length']
        )
        
        if source:
            print(f"  使用されたタグ: {source}")
            print(f"  元の文字数: {original_length:,}文字")
            print(f"  最終文字数: {final_length:,}文字")
            if original_length > test_case['max_length']:
                print(f"  ⚠️  文字数制限により切り詰められました")
            print(f"  最初の100文字: {text[:100]}...")
        else:
            print(f"  ❌ 抽出失敗（指定されたタグが見つかりません）")

except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()