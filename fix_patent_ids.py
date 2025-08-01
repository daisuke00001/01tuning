#!/usr/bin/env python3
"""
既存データのpatent_idを修正するスクリプト
"""

import json
import re
from pathlib import Path
from collections import defaultdict

def fix_patent_ids():
    """空のpatent_idを修正してユニークなIDを割り当て"""
    
    print("🛠️ Patent ID修正処理")
    print("=" * 50)
    
    # 元データを読み込み
    input_path = Path("data/cleaned/cleaned_patents_medium.json")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 元データ数: {len(data)}")
    
    # コンテンツベースでpatent_idを生成
    content_groups = defaultdict(list)
    
    # セクション別にグループ化してpatent境界を推測
    current_patent = []
    patent_groups = []
    
    # セクションの順序でpatent境界を推測
    section_order = ['abstract', 'technical_field', 'background_art', 'detailed_description', 'title']
    
    for i, item in enumerate(data):
        section = item.get('section', '')
        
        # 新しい特許の開始を検出（abstractまたはtitleから始まる）
        if section in ['abstract', 'title'] and current_patent:
            # 前の特許を保存
            patent_groups.append(current_patent)
            current_patent = []
        
        current_patent.append(item)
    
    # 最後の特許も追加
    if current_patent:
        patent_groups.append(current_patent)
    
    print(f"📋 推測された特許数: {len(patent_groups)}")
    
    # 各グループにユニークなpatent_idを割り当て
    fixed_data = []
    
    for group_idx, patent_group in enumerate(patent_groups):
        # 特許IDを生成（内容のハッシュベース）
        content_hash = ""
        for item in patent_group:
            text = item.get('text', '')
            content_hash += text[:100]  # 最初の100文字を使用
        
        # ハッシュからユニークIDを生成
        patent_id = f"JP{abs(hash(content_hash)) % 1000000:06d}"
        
        print(f"🔧 グループ {group_idx+1}: {len(patent_group)}セクション → {patent_id}")
        
        # 各アイテムにpatent_idを設定
        for item in patent_group:
            item['patent_id'] = patent_id
            fixed_data.append(item)
    
    # 修正データを保存
    output_path = Path("data/cleaned/fixed_patents_medium.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 修正データを保存: {output_path}")
    
    # 統計表示
    patent_count = {}
    for item in fixed_data:
        pid = item['patent_id']
        patent_count[pid] = patent_count.get(pid, 0) + 1
    
    print(f"\n📈 修正後統計:")
    print(f"  - 総データ数: {len(fixed_data)}")
    print(f"  - ユニークpatent_id数: {len(patent_count)}")
    print(f"  - 平均セクション数/特許: {len(fixed_data) / len(patent_count):.1f}")
    
    print(f"\n🔍 Patent ID分布:")
    for pid, count in list(patent_count.items())[:5]:
        print(f"  {pid}: {count}セクション")
    
    return output_path

def create_enhanced_data_with_claims():
    """修正されたデータからclaims統合版を作成"""
    
    print(f"\n🚀 Claims統合版作成")
    print("=" * 50)
    
    # 修正データを読み込み
    fixed_path = Path("data/cleaned/fixed_patents_medium.json")
    with open(fixed_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # patent_idでグループ化
    patents_by_id = {}
    for item in data:
        patent_id = item['patent_id']
        if patent_id not in patents_by_id:
            patents_by_id[patent_id] = []
        patents_by_id[patent_id].append(item)
    
    # 統合claimsセクションを追加
    enhanced_data = list(data)  # 元データをコピー
    
    for patent_id, sections in patents_by_id.items():
        # 請求項セクション(claim_N)を検索
        claim_sections = []
        for section in sections:
            section_name = section.get('section', '')
            if section_name.startswith('claim_'):
                # claim番号を抽出
                claim_match = re.match(r'claim_(\d+)', section_name)
                if claim_match:
                    claim_number = claim_match.group(1)
                    claim_text = section.get('text', '')
                    if claim_text:
                        claim_sections.append({
                            'number': claim_number,
                            'text': claim_text
                        })
        
        # 請求項が見つかった場合、統合claimsセクションを作成
        if claim_sections:
            # 番号順にソート
            claim_sections.sort(key=lambda x: int(x['number']))
            
            # 【請求項N】形式で統合
            combined_claims = []
            for claim in claim_sections:
                formatted_claim = f"【請求項{claim['number']}】{claim['text']}"
                combined_claims.append(formatted_claim)
            
            # 統合claimsセクションを追加
            integrated_claims = {
                'patent_id': patent_id,
                'section': 'claims',
                'text': '\n'.join(combined_claims)
            }
            enhanced_data.append(integrated_claims)
            
            print(f"✅ {patent_id}: {len(claim_sections)}個の請求項を統合")
    
    # 拡張データを保存
    enhanced_path = Path("data/cleaned/fixed_enhanced_patents_medium.json")
    with open(enhanced_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 拡張データを保存: {enhanced_path}")
    print(f"📊 拡張データ数: {len(enhanced_data)}")
    
    return enhanced_path

if __name__ == "__main__":
    # Step 1: Patent ID修正
    fixed_path = fix_patent_ids()
    
    # Step 2: Claims統合
    enhanced_path = create_enhanced_data_with_claims()
    
    print(f"\n✅ 修正完了！")
    print(f"  修正データ: {fixed_path}")
    print(f"  拡張データ: {enhanced_path}")