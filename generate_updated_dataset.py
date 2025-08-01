#!/usr/bin/env python3
"""段落番号付きデータセットの生成"""

import sys
sys.path.append('/mnt/d/20250728/01tuning')

import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 修正されたProcessorを使用するため、直接importが必要
# ここでは簡易版で実装
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime

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
    
    for child in element:
        if child.tag.endswith('}P'):
            # 段落番号を取得
            p_number = child.get('{http://www.wipo.int/standards/XMLSchema/ST96/Common}pNumber')
            if not p_number:
                p_number = child.get('pNumber')
            
            # 段落のテキストを取得
            p_text = ET.tostring(child, encoding='unicode', method='text')
            p_text = clean_xml_text(p_text)
            
            if p_text:
                if p_number:
                    text_parts.append(f"【{p_number}】\n{p_text}")
                else:
                    text_parts.append(p_text)
        else:
            child_text = extract_text_with_paragraph_numbers(child)
            if child_text:
                text_parts.append(child_text)
    
    if element.text and element.text.strip():
        text_parts.insert(0, element.text.strip())
    
    return '\n\n'.join(text_parts)

def parse_patent_xml(xml_path):
    """特許XMLファイルを解析"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 基本情報の取得
        patent_number_elem = root.find('.//pat:PublicationNumber', namespaces)
        patent_number = patent_number_elem.text if patent_number_elem is not None else ""
        
        title_elem = root.find('.//pat:InventionTitle', namespaces)
        title = title_elem.text if title_elem is not None else ""
        
        # 請求項の抽出
        claims = []
        claims_elem = root.find('.//pat:Claims', namespaces)
        if claims_elem is not None:
            for claim in claims_elem.findall('.//pat:Claim', namespaces):
                claim_num_elem = claim.find('.//pat:ClaimNumber', namespaces)
                claim_text_elem = claim.find('.//pat:ClaimText', namespaces)
                if claim_text_elem is not None:
                    claim_num = claim_num_elem.text if claim_num_elem is not None else ""
                    claim_text = ET.tostring(claim_text_elem, encoding='unicode', method='text')
                    claims.append({
                        'claim_number': claim_num,
                        'claim_text': clean_xml_text(claim_text)
                    })
        
        # 実施形態の抽出（段落番号付き）
        detailed_description = ""
        # EmbodimentDescription優先
        embodiment_elem = root.find('.//pat:EmbodimentDescription', namespaces)
        if embodiment_elem is not None:
            detailed_description = extract_text_with_paragraph_numbers(embodiment_elem)
        
        # 見つからない場合はBestMode
        if not detailed_description:
            best_mode_elem = root.find('.//pat:BestMode', namespaces)
            if best_mode_elem is not None:
                detailed_description = extract_text_with_paragraph_numbers(best_mode_elem)
        
        # さらに見つからない場合はInventionMode
        if not detailed_description:
            invention_mode_elem = root.find('.//jppat:InventionMode', namespaces)
            if invention_mode_elem is not None:
                detailed_description = extract_text_with_paragraph_numbers(invention_mode_elem)
        
        return {
            'patent_number': patent_number,
            'title': title,
            'claims': claims,
            'detailed_description': detailed_description
        }
        
    except Exception as e:
        print(f"エラー: {xml_path}: {e}")
        return None

def create_chatml_dataset(patents, output_path):
    """ChatML形式のデータセット作成"""
    chatml_data = []
    
    for patent in patents:
        if not patent:
            continue
            
        patent_id = patent.get('patent_number', '')
        claims = patent.get('claims', [])
        detailed_description = patent.get('detailed_description', '')
        
        # 実施形態と請求項が両方存在する場合のみ学習データを作成
        if detailed_description.strip() and claims:
            # 全請求項をまとめる
            all_claims_text = ""
            for claim in claims:
                claim_text = claim.get('claim_text', '')
                claim_number = claim.get('claim_number', '')
                if claim_text.strip():
                    all_claims_text += f"【請求項{claim_number}】\n{claim_text}\n\n"
            
            if all_claims_text.strip():
                chatml_record = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "あなたは特許文書の専門家です。与えられた特許請求の範囲に基づいて、その発明を実施するための具体的な形態を詳しく説明してください。"
                        },
                        {
                            "role": "user",
                            "content": f"以下の特許請求の範囲に基づいて、発明を実施するための形態を説明してください：\n\n{all_claims_text.strip()}"
                        },
                        {
                            "role": "assistant",
                            "content": f"【発明を実施するための形態】\n\n{detailed_description}"
                        }
                    ],
                    "metadata": {
                        "patent_id": patent_id,
                        "claims_count": len(claims),
                        "paragraph_numbers_included": True,
                        "created_at": datetime.now().isoformat()
                    }
                }
                
                chatml_data.append(chatml_record)
    
    # JSON出力
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chatml_data, f, ensure_ascii=False, indent=2)
    
    return len(chatml_data)

# メイン処理
jpb_dir = Path("/mnt/d/20250728/01tuning/data/JPB_2025018_0130発行分/DOCUMENT")
output_dir = Path("/mnt/d/20250728/01tuning/data/processed")

print("段落番号付きデータセット生成開始")
print("=" * 80)

# 全XMLファイルを処理
xml_files = list(jpb_dir.glob("**/*.xml"))
print(f"処理対象ファイル数: {len(xml_files)}")

patents = []
for i, xml_file in enumerate(xml_files):
    if i % 10 == 0:
        print(f"進捗: {i}/{len(xml_files)}")
    
    patent_data = parse_patent_xml(xml_file)
    if patent_data:
        patents.append(patent_data)

print(f"解析成功: {len(patents)}件")

# ChatMLデータセット作成
output_file = output_dir / "chatml_training_with_paragraphs_full.json"
chatml_count = create_chatml_dataset(patents, output_file)

print(f"ChatMLデータセット作成完了:")
print(f"  出力ファイル: {output_file}")
print(f"  生成データ数: {chatml_count}")

# 段落番号が含まれているか確認
if output_file.exists():
    with open(output_file, 'r', encoding='utf-8') as f:
        sample_data = json.load(f)
    
    if sample_data:
        first_assistant = None
        for msg in sample_data[0]['messages']:
            if msg['role'] == 'assistant':
                first_assistant = msg['content']
                break
        
        if first_assistant:
            paragraph_count = len(re.findall(r'【\d{4}】', first_assistant))
            print(f"  サンプル確認: {paragraph_count}個の段落番号を確認")
            print(f"  最初の200文字: {first_assistant[:200]}...")