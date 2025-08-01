#!/usr/bin/env python3
"""
既存データから統合claimsセクションを作成してテストするスクリプト
"""

import json
from pathlib import Path
import re

def simulate_claims_integration():
    """既存の個別請求項から統合claimsセクションを作成"""
    
    print("🧪 Claims統合シミュレーション")
    print("=" * 50)
    
    # 既存データを読み込み
    data_path = Path("data/cleaned/cleaned_patents_medium.json")
    if not data_path.exists():
        print(f"❌ データファイルが見つかりません: {data_path}")
        return
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 元データ: {len(data)}件")
    
    # patent_idでグループ化
    patents_by_id = {}
    for item in data:
        patent_id = item.get('patent_id', 'unknown')
        if patent_id not in patents_by_id:
            patents_by_id[patent_id] = []
        patents_by_id[patent_id].append(item)
    
    print(f"📋 特許数: {len(patents_by_id)}件")
    
    # 統合claimsセクションを作成
    enhanced_data = []
    patents_with_claims = 0
    total_claims_added = 0
    
    for patent_id, sections in patents_by_id.items():
        # 既存セクションをそのまま追加
        enhanced_data.extend(sections)
        
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
            
            patents_with_claims += 1
            total_claims_added += 1
            
            print(f"✅ {patent_id}: {len(claim_sections)}個の請求項を統合")
    
    print(f"\n📈 統計:")
    print(f"  - 元データ数: {len(data)}")
    print(f"  - 拡張データ数: {len(enhanced_data)}")
    print(f"  - 請求項を持つ特許: {patents_with_claims}")
    print(f"  - 追加されたclaims: {total_claims_added}")
    
    # 拡張データを保存
    output_path = Path("data/cleaned/enhanced_patents_medium.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 拡張データを保存: {output_path}")
    
    # サンプル表示
    if enhanced_data:
        print(f"\n📋 統合claimsサンプル:")
        for item in enhanced_data:
            if item.get('section') == 'claims':
                print(f"特許ID: {item.get('patent_id')}")
                claims_text = item.get('text', '')
                print(f"統合請求項: {claims_text[:200]}...")
                break
    
    return output_path

def test_convert_with_enhanced_data():
    """拡張データでchat format変換をテスト"""
    
    print("\n🚀 Chat Format変換テスト")
    print("=" * 50)
    
    # 拡張データパスを設定
    enhanced_path = Path("data/cleaned/enhanced_patents_medium.json")
    
    if not enhanced_path.exists():
        print(f"❌ 拡張データが見つかりません: {enhanced_path}")
        return
    
    # convert_to_chat_format.pyをインポートして実行
    try:
        import sys
        sys.path.append('scripts')
        from scripts.convert_to_chat_format import PatentChatFormatter
        
        formatter = PatentChatFormatter()
        
        # 拡張データを使用してテスト変換
        formatter.convert_to_chat_format("enhanced_patents_medium.json", "test_chat_enhanced.json")
        
        print("✅ Chat format変換テスト完了")
        
    except Exception as e:
        print(f"❌ Chat format変換エラー: {e}")

if __name__ == "__main__":
    # Step 1: Claims統合
    enhanced_path = simulate_claims_integration()
    
    # Step 2: Chat format変換テスト
    test_convert_with_enhanced_data()