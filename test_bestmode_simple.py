#!/usr/bin/env python3
"""BestMode追加の効果を簡易テスト"""

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

def extract_detailed_description_old(root):
    """旧バージョン（BestModeなし）"""
    # EmbodimentDescription
    embodiment_elem = root.find('.//pat:EmbodimentDescription', namespaces)
    if embodiment_elem is not None:
        text = ET.tostring(embodiment_elem, encoding='unicode', method='text')
        return clean_xml_text(text)
    
    # DetailedDescription
    desc_elem = root.find('.//pat:DetailedDescription', namespaces)
    if desc_elem is not None:
        text = ET.tostring(desc_elem, encoding='unicode', method='text')
        return clean_xml_text(text)
    
    return ""

def extract_detailed_description_new(root):
    """新バージョン（BestMode追加）"""
    # EmbodimentDescription
    embodiment_elem = root.find('.//pat:EmbodimentDescription', namespaces)
    if embodiment_elem is not None:
        text = ET.tostring(embodiment_elem, encoding='unicode', method='text')
        return clean_xml_text(text)
    
    # DetailedDescription
    desc_elem = root.find('.//pat:DetailedDescription', namespaces)
    if desc_elem is not None:
        text = ET.tostring(desc_elem, encoding='unicode', method='text')
        return clean_xml_text(text)
    
    # BestMode（新規追加）
    best_mode_elem = root.find('.//pat:BestMode', namespaces)
    if best_mode_elem is not None:
        text = ET.tostring(best_mode_elem, encoding='unicode', method='text')
        return clean_xml_text(text)
    
    return ""

# テスト対象の問題ファイル
test_file = "/mnt/d/20250728/01tuning/data/JPB_2025018_0130発行分/DOCUMENT/P_B1/0007624101/0007624191/0007624195/0007624195.xml"

print("BestMode追加前後の比較テスト")
print("=" * 80)
print(f"テストファイル: {Path(test_file).name}")

try:
    tree = ET.parse(test_file)
    root = tree.getroot()
    
    # 特許番号
    patent_number_elem = root.find('.//pat:PublicationNumber', namespaces)
    patent_number = patent_number_elem.text if patent_number_elem is not None else "N/A"
    print(f"特許番号: {patent_number}")
    
    # 旧バージョンでの抽出
    old_desc = extract_detailed_description_old(root)
    print(f"\n【旧バージョン（BestModeなし）】")
    print(f"  抽出文字数: {len(old_desc)}文字")
    print(f"  抽出可否: {'❌ 除外される' if len(old_desc) == 0 else '✅ 処理される'}")
    
    # 新バージョンでの抽出
    new_desc = extract_detailed_description_new(root)
    print(f"\n【新バージョン（BestMode追加）】")
    print(f"  抽出文字数: {len(new_desc)}文字")
    print(f"  抽出可否: {'❌ 除外される' if len(new_desc) == 0 else '✅ 処理される'}")
    
    # 差分
    if len(old_desc) == 0 and len(new_desc) > 0:
        print(f"\n🎉 このファイルは救済されました！")
        print(f"  BestModeから{len(new_desc)}文字を抽出")
        print(f"  内容の先頭200文字:")
        print(f"  {new_desc[:200]}...")
        
        # BestModeの存在確認
        best_mode_elem = root.find('.//pat:BestMode', namespaces)
        if best_mode_elem is not None:
            print(f"\n  BestModeタグ: ✅ 存在")
    
    # 各タグの存在確認
    print(f"\n【タグ存在確認】")
    tags = [
        ('EmbodimentDescription', './/pat:EmbodimentDescription'),
        ('DetailedDescription', './/pat:DetailedDescription'),
        ('BestMode', './/pat:BestMode'),
        ('InventionMode', './/jppat:InventionMode')
    ]
    
    for tag_name, xpath in tags:
        elem = root.find(xpath, namespaces)
        if elem is not None:
            text = ET.tostring(elem, encoding='unicode', method='text')
            text_length = len(clean_xml_text(text))
            print(f"  {tag_name}: ✅ 存在（{text_length}文字）")
        else:
            print(f"  {tag_name}: ❌ なし")

except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()