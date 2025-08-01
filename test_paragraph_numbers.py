#!/usr/bin/env python3
"""段落番号【XXXX】保持機能のテスト"""

import xml.etree.ElementTree as ET
import re
from pathlib import Path

# 名前空間定義
namespaces = {
    'jppat': 'http://www.jpo.go.jp/standards/XMLSchema/ST96/JPPatent',
    'jpcom': 'http://www.jpo.go.jp/standards/XMLSchema/ST96/JPCommon',
    'com': 'http://www.wipo.int/standards/XMLSchema/ST96/Common',
    'pat': 'http://www.wipo.int/standards/XMLSchema/ST96/Patent'
}

def clean_xml_text(text):
    """XMLから抽出したテキストのクリーニング"""
    if not text:
        return ""
    
    # XMLタグの除去と改行の正規化
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'<com:Br\s*/>', '\n', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_text_with_paragraph_numbers(element):
    """段落番号【XXXX】を含めてテキストを抽出"""
    if element is None:
        return ""
    
    text_parts = []
    
    # 直接の子要素を処理
    for child in element:
        if child.tag.endswith('}P'):  # com:P または pat:P
            # 段落番号を取得
            p_number = child.get('{http://www.wipo.int/standards/XMLSchema/ST96/Common}pNumber')
            if not p_number:
                p_number = child.get('pNumber')  # 名前空間なしも試行
            
            # 段落のテキストを取得
            p_text = ET.tostring(child, encoding='unicode', method='text')
            p_text = clean_xml_text(p_text)
            
            if p_text:
                if p_number:
                    # 段落番号付きで追加
                    text_parts.append(f"【{p_number}】\n{p_text}")
                else:
                    # 段落番号なしで追加
                    text_parts.append(p_text)
        else:
            # P以外のタグは再帰処理
            child_text = extract_text_with_paragraph_numbers(child)
            if child_text:
                text_parts.append(child_text)
    
    # 直接テキストがある場合も含める
    if element.text and element.text.strip():
        text_parts.insert(0, element.text.strip())
    
    return '\n\n'.join(text_parts)

# テストファイル
test_file = "/mnt/d/20250728/01tuning/data/JPB_2025018_0130発行分/DOCUMENT/P_B1/0007620301/0007620361/0007620367/0007620367.xml"

print("段落番号【XXXX】保持機能のテスト")
print("=" * 80)
print(f"テストファイル: {Path(test_file).name}")

try:
    tree = ET.parse(test_file)
    root = tree.getroot()
    
    # 特許番号
    patent_number_elem = root.find('.//pat:PublicationNumber', namespaces)
    patent_number = patent_number_elem.text if patent_number_elem is not None else "N/A"
    print(f"特許番号: {patent_number}")
    
    # 1. 従来の抽出方法（段落番号なし）
    embodiment_elem = root.find('.//pat:EmbodimentDescription', namespaces)
    if embodiment_elem is not None:
        old_text = ET.tostring(embodiment_elem, encoding='unicode', method='text')
        old_text = clean_xml_text(old_text)
        print(f"\n【従来方法（段落番号なし）】")
        print(f"文字数: {len(old_text)}")
        print(f"最初の200文字:\n{old_text[:200]}...")
        
        # 段落番号パターンを検索
        paragraph_markers = re.findall(r'【\d{4}】', old_text)
        print(f"段落番号【XXXX】の数: {len(paragraph_markers)}")
    
    # 2. 新しい抽出方法（段落番号付き）
    if embodiment_elem is not None:
        new_text = extract_text_with_paragraph_numbers(embodiment_elem)
        print(f"\n【新方法（段落番号付き）】")
        print(f"文字数: {len(new_text)}")
        print(f"最初の500文字:\n{new_text[:500]}...")
        
        # 段落番号パターンを検索
        paragraph_markers = re.findall(r'【\d{4}】', new_text)
        print(f"段落番号【XXXX】の数: {len(paragraph_markers)}")
        if paragraph_markers:
            print(f"最初の10個: {paragraph_markers[:10]}")
        
        # 改善されたかチェック
        if len(paragraph_markers) > 0:
            print(f"\n✅ 成功！段落番号が正しく抽出されました")
        else:
            print(f"\n❌ 失敗：段落番号が抽出されませんでした")

except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()