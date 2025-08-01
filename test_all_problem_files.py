#!/usr/bin/env python3
"""全ての問題ファイルでBestModeの効果を確認"""

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

def extract_with_bestmode(root):
    """BestMode追加版の抽出"""
    # EmbodimentDescription
    elem = root.find('.//pat:EmbodimentDescription', namespaces)
    if elem is not None:
        return len(clean_xml_text(ET.tostring(elem, encoding='unicode', method='text')))
    
    # DetailedDescription
    elem = root.find('.//pat:DetailedDescription', namespaces)
    if elem is not None:
        return len(clean_xml_text(ET.tostring(elem, encoding='unicode', method='text')))
    
    # BestMode
    elem = root.find('.//pat:BestMode', namespaces)
    if elem is not None:
        return len(clean_xml_text(ET.tostring(elem, encoding='unicode', method='text')))
    
    return 0

def extract_with_invention_mode(root):
    """BestMode + InventionMode版の抽出"""
    # EmbodimentDescription
    elem = root.find('.//pat:EmbodimentDescription', namespaces)
    if elem is not None:
        return len(clean_xml_text(ET.tostring(elem, encoding='unicode', method='text')))
    
    # DetailedDescription
    elem = root.find('.//pat:DetailedDescription', namespaces)
    if elem is not None:
        return len(clean_xml_text(ET.tostring(elem, encoding='unicode', method='text')))
    
    # BestMode
    elem = root.find('.//pat:BestMode', namespaces)
    if elem is not None:
        return len(clean_xml_text(ET.tostring(elem, encoding='unicode', method='text')))
    
    # InventionMode
    elem = root.find('.//jppat:InventionMode', namespaces)
    if elem is not None:
        return len(clean_xml_text(ET.tostring(elem, encoding='unicode', method='text')))
    
    return 0

# 問題のあった6つのファイル
problem_files = [
    ("0007624195", "/mnt/d/20250728/01tuning/data/JPB_2025018_0130発行分/DOCUMENT/P_B1/0007624101/0007624191/0007624195/0007624195.xml"),
    ("0007624219", None),  # パスは後で検索
    ("0007624238", None),
    ("0007624240", None),
    ("0007624294", None),
    ("0007624185000001", None),  # 特殊なファイル
]

print("全問題ファイルのBestMode救済効果")
print("=" * 100)
print(f"{'ファイル名':>20} | {'特許番号':>10} | {'EmbDesc':>8} | {'DetDesc':>8} | {'BestMode':>8} | {'InvMode':>8} | {'救済':>6}")
print("-" * 100)

rescued_count = 0
jpb_dir = Path("/mnt/d/20250728/01tuning/data/JPB_2025018_0130発行分/DOCUMENT")

for filename, filepath in problem_files:
    # ファイルパスが未定の場合は検索
    if filepath is None:
        files = list(jpb_dir.glob(f"**/{filename}.xml"))
        if not files:
            print(f"{filename:>20} | {'検索失敗':>10} | {'-':>8} | {'-':>8} | {'-':>8} | {'-':>8} | {'?':>6}")
            continue
        filepath = str(files[0])
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # 特許番号
        elem = root.find('.//pat:PublicationNumber', namespaces)
        patent_number = elem.text if elem is not None else "N/A"
        
        # 各セクションの文字数
        lengths = {}
        tags = [
            ('EmbDesc', './/pat:EmbodimentDescription'),
            ('DetDesc', './/pat:DetailedDescription'),
            ('BestMode', './/pat:BestMode'),
            ('InvMode', './/jppat:InventionMode')
        ]
        
        for tag_name, xpath in tags:
            elem = root.find(xpath, namespaces)
            if elem is not None:
                text = ET.tostring(elem, encoding='unicode', method='text')
                lengths[tag_name] = len(clean_xml_text(text))
            else:
                lengths[tag_name] = 0
        
        # BestMode追加による救済判定
        rescued_bestmode = (lengths['EmbDesc'] == 0 and 
                           lengths['DetDesc'] == 0 and 
                           lengths['BestMode'] > 0)
        
        # InventionMode追加による救済判定
        rescued_invention = (lengths['EmbDesc'] == 0 and 
                            lengths['DetDesc'] == 0 and 
                            lengths['BestMode'] == 0 and
                            lengths['InvMode'] > 0)
        
        if rescued_bestmode:
            rescued_count += 1
            status = "✅(BM)"
        elif rescued_invention:
            rescued_count += 1
            status = "✅(IM)"
        else:
            status = "❌"
        
        print(f"{filename:>20} | {patent_number:>10} | {lengths['EmbDesc']:>8} | {lengths['DetDesc']:>8} | {lengths['BestMode']:>8} | {lengths['InvMode']:>8} | {status:>6}")
        
    except Exception as e:
        print(f"{filename:>20} | {'エラー':>10} | {'-':>8} | {'-':>8} | {'-':>8} | {'-':>8} | {'?':>6}")

print("-" * 100)
print(f"\n【段階2: BestMode + InventionMode追加の効果】")
print(f"  問題ファイル数: 6")
print(f"  救済されたファイル: {rescued_count}")
print(f"  救済率: {rescued_count/6*100:.1f}%")
print(f"\n  全体への影響:")
print(f"    変更前: 194/200 (97.0%)")
print(f"    変更後: {194 + rescued_count}/200 ({(194 + rescued_count)/200*100:.1f}%)")