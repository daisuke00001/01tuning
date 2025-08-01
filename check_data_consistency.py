#!/usr/bin/env python3
"""
データの整合性をチェックするスクリプト
"""

import json
from pathlib import Path

def check_data_consistency():
    """データの整合性をチェック"""
    
    print("🔍 データ整合性チェック")
    print("=" * 60)
    
    # 拡張データを読み込み
    enhanced_path = Path("data/cleaned/enhanced_patents_medium.json")
    if not enhanced_path.exists():
        print(f"❌ ファイルが見つかりません: {enhanced_path}")
        return
    
    with open(enhanced_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 総データ数: {len(data)}")
    
    # patent_idでグループ化
    patents_by_id = {}
    for item in data:
        patent_id = item.get('patent_id', 'unknown')
        if patent_id not in patents_by_id:
            patents_by_id[patent_id] = {}
        
        section = item.get('section', 'unknown')
        text = item.get('text', '')
        patents_by_id[patent_id][section] = text
    
    print(f"📋 特許数: {len(patents_by_id)}")
    
    # 各特許の内容をチェック
    for patent_id, sections in patents_by_id.items():
        print(f"\n🔍 特許ID: {patent_id}")
        print(f"   セクション数: {len(sections)}")
        print(f"   利用可能セクション: {list(sections.keys())}")
        
        # claimsとdetailed_descriptionの内容をチェック
        claims_text = sections.get('claims', '')
        detailed_desc = sections.get('detailed_description', '')
        
        if claims_text and detailed_desc:
            print(f"\n   📜 請求項 (最初の100文字):")
            print(f"   {claims_text[:100]}...")
            
            print(f"\n   📋 実施形態 (最初の100文字):")
            print(f"   {detailed_desc[:100]}...")
            
            # キーワード一致チェック
            claims_keywords = extract_keywords(claims_text)
            desc_keywords = extract_keywords(detailed_desc)
            
            common_keywords = claims_keywords & desc_keywords
            print(f"\n   🔗 共通キーワード: {list(common_keywords)[:5]}")
            
            if len(common_keywords) < 2:
                print(f"   ⚠️  整合性問題の可能性: 共通キーワードが少ない ({len(common_keywords)}個)")
            else:
                print(f"   ✅ 整合性OK: 十分な共通キーワード ({len(common_keywords)}個)")
    
    # Chat formatデータをチェック
    print(f"\n" + "=" * 60)
    print("🎯 Chat Formatデータの整合性チェック")
    
    chat_path = Path("data/chat_format/test_chat_enhanced.json")
    if chat_path.exists():
        with open(chat_path, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
        
        print(f"📊 Chat formatデータ数: {len(chat_data)}")
        
        for i, item in enumerate(chat_data):
            text = item.get('text', '')
            patent_id = item.get('patent_id', 'unknown')
            
            print(f"\n🔍 Chat Format #{i+1} (特許ID: {patent_id}):")
            
            # userとassistantの内容を抽出
            user_content = extract_user_content(text)
            assistant_content = extract_assistant_content(text)
            
            if user_content and assistant_content:
                print(f"   👤 User (請求項): {user_content[:80]}...")
                print(f"   🤖 Assistant (実施形態): {assistant_content[:80]}...")
                
                # キーワード一致チェック
                user_keywords = extract_keywords(user_content)
                assistant_keywords = extract_keywords(assistant_content)
                common = user_keywords & assistant_keywords
                
                print(f"   🔗 共通キーワード: {list(common)[:3]}")
                
                if len(common) < 2:
                    print(f"   ⚠️  整合性問題: userとassistantの内容が一致しない可能性")
                else:
                    print(f"   ✅ 整合性OK")

def extract_keywords(text):
    """テキストからキーワードを抽出"""
    import re
    
    # 日本語の単語を抽出（ひらがな・カタカナ・漢字3文字以上）
    keywords = set()
    
    # 漢字3文字以上
    kanji_words = re.findall(r'[一-龯]{3,}', text)
    keywords.update(kanji_words)
    
    # カタカナ3文字以上
    katakana_words = re.findall(r'[ア-ン]{3,}', text)
    keywords.update(katakana_words)
    
    # 【】内のキーワード
    bracket_words = re.findall(r'【([^】]+)】', text)
    keywords.update(bracket_words)
    
    return keywords

def extract_user_content(chat_text):
    """Chat textからuser部分を抽出"""
    import re
    match = re.search(r'<\|im_start\|>user\n(.*?)<\|im_end\|>', chat_text, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_assistant_content(chat_text):
    """Chat textからassistant部分を抽出"""
    import re
    match = re.search(r'<\|im_start\|>assistant\n(.*?)<\|im_end\|>', chat_text, re.DOTALL)
    return match.group(1).strip() if match else ""

if __name__ == "__main__":
    check_data_consistency()