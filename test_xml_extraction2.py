#!/usr/bin/env python3
"""複数のXMLファイルをテストして除外条件を調査"""

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

def analyze_xml_file(xml_path):
    """XMLファイルを分析して除外条件をチェック"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 特許番号
        patent_number_elem = root.find('.//pat:PublicationNumber', namespaces)
        patent_number = patent_number_elem.text if patent_number_elem is not None else "N/A"
        
        # 請求項
        claims = []
        claims_elem = root.find('.//pat:Claims', namespaces)
        if claims_elem is not None:
            for claim in claims_elem.findall('.//pat:Claim', namespaces):
                claim_text_elem = claim.find('.//pat:ClaimText', namespaces)
                if claim_text_elem is not None:
                    claims.append({'claim_text': 'exists'})
        
        # EmbodimentDescription
        embodiment_elem = root.find('.//pat:EmbodimentDescription', namespaces)
        embodiment_text = ""
        if embodiment_elem is not None:
            embodiment_text = ET.tostring(embodiment_elem, encoding='unicode', method='text')
            embodiment_text = clean_xml_text(embodiment_text)
        
        # DetailedDescription（フォールバック）
        detailed_elem = root.find('.//pat:DetailedDescription', namespaces)
        detailed_text = ""
        if detailed_elem is not None:
            detailed_text = ET.tostring(detailed_elem, encoding='unicode', method='text')
            detailed_text = clean_xml_text(detailed_text)
        
        # 最終的なdetailed_description
        detailed_description = embodiment_text if embodiment_text else detailed_text
        
        # 条件チェック
        condition1 = bool(detailed_description.strip())
        condition2 = bool(claims)
        will_process = condition1 and condition2
        
        return {
            'file': xml_path.name,
            'patent_number': patent_number,
            'has_claims': condition2,
            'claims_count': len(claims),
            'has_detailed_desc': condition1,
            'desc_length': len(detailed_description),
            'has_embodiment': bool(embodiment_text),
            'has_detailed': bool(detailed_text),
            'will_process': will_process
        }
    except Exception as e:
        return {
            'file': xml_path.name,
            'error': str(e)
        }

# JPBディレクトリから最初の20個のXMLファイルを取得
jpb_dir = Path("/mnt/d/20250728/01tuning/data/JPB_2025018_0130発行分/DOCUMENT")
xml_files = list(jpb_dir.glob("**/*.xml"))[:200]

print(f"JPBディレクトリから{len(xml_files)}個のXMLファイルを分析します")
print("=" * 100)

# 統計
total_files = 0
processed_count = 0
excluded_count = 0
no_claims = 0
no_desc = 0

print(f"{'ファイル名':>20} | {'特許番号':>10} | {'請求項':>6} | {'説明':>6} | {'処理':>4} | {'理由':>30}")
print("-" * 100)

for xml_file in xml_files:
    result = analyze_xml_file(xml_file)
    
    if 'error' in result:
        print(f"{result['file']:>20} | ERROR: {result['error']}")
        continue
    
    total_files += 1
    
    if result['will_process']:
        processed_count += 1
        status = "✅"
        reason = "正常"
    else:
        excluded_count += 1
        status = "❌"
        reasons = []
        if not result['has_claims']:
            no_claims += 1
            reasons.append("請求項なし")
        if not result['has_detailed_desc']:
            no_desc += 1
            reasons.append(f"説明なし(emb:{result['has_embodiment']},det:{result['has_detailed']})")
        reason = ", ".join(reasons)
    
    print(f"{result['file']:>20} | {result['patent_number']:>10} | {result['claims_count']:>6} | {result['desc_length']:>6} | {status:>4} | {reason:>30}")

print("-" * 100)
print(f"\n統計:")
print(f"  総ファイル数: {total_files}")
print(f"  処理される: {processed_count} ({processed_count/total_files*100:.1f}%)")
print(f"  除外される: {excluded_count} ({excluded_count/total_files*100:.1f}%)")
print(f"    - 請求項なし: {no_claims}")
print(f"    - 説明なし: {no_desc}")

if excluded_count > 0:
    print(f"\n⚠️  {excluded_count}個のファイルが除外されています！")
    print("これが200件→2件になる原因の可能性があります。")