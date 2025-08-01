#!/usr/bin/env python3
"""
特許文書の正規表現パターンをテストするスクリプト
"""

import re

# 定数定義（convert_to_chat_format.pyと同じ）
PATENT_MARKER_PATTERN = r'【[^】]*】'  # 【課題】【解決手段】等の一般マーカー
PATENT_PARAGRAPH_PATTERN = r'【\d{4}】'  # 【0010】【0011】等の段落番号
PATENT_SECTION_PATTERN = r'【[^】\d][^】]*】'  # 【発明を実施する形態】等のセクション名（数字以外で始まる）
PATENT_ALL_PATTERN = r'【[^】]*】'  # 全ての【】パターン（統合）

def test_patent_patterns():
    """特許文書パターンのテスト"""
    
    print("🧪 特許文書の正規表現パターンテスト")
    print("=" * 60)
    
    # テストデータ
    test_samples = [
        # 請求項データ
        {
            "type": "請求項",
            "text": "【請求項1】精神障害分析装置において、【請求項2】前記装置は、【課題】精神障害であることを分析する"
        },
        
        # 実施形態データ
        {
            "type": "実施形態", 
            "text": "【発明を実施する形態】【0010】本発明の実施形態を説明する。【0011】図1に示すように装置は、【0012】センサ部を含む。"
        },
        
        # 混合データ
        {
            "type": "混合",
            "text": "【課題】【0001】従来技術では【解決手段】【0002】本発明では【発明を実施する形態】【0010】実施形態1"
        }
    ]
    
    # 各パターンでテスト
    patterns = [
        ("一般マーカー", PATENT_MARKER_PATTERN),
        ("段落番号", PATENT_PARAGRAPH_PATTERN), 
        ("セクション名", PATENT_SECTION_PATTERN),
        ("全パターン", PATENT_ALL_PATTERN)
    ]
    
    for sample in test_samples:
        print(f"\n📊 {sample['type']}データのテスト:")
        print(f"入力: {sample['text'][:100]}...")
        
        for pattern_name, pattern in patterns:
            matches = re.findall(pattern, sample['text'])
            split_result = re.split(pattern, sample['text'])
            
            print(f"\n  {pattern_name} ({pattern}):")
            print(f"    マッチ: {matches}")
            print(f"    分割数: {len(split_result)} 部分")
            if len(split_result) > 1:
                print(f"    分割例: {split_result[1][:50]}..." if len(split_result[1]) > 0 else "    分割例: (空)")
    
    print("\n" + "=" * 60)
    
    # 特定パターンのテスト
    print("🎯 特定パターンの詳細テスト:")
    
    # 段落番号パターン
    paragraph_text = "【0010】最初の段落【0011】二番目の段落【0012】三番目の段落"
    print(f"\n📝 段落番号テスト:")
    print(f"入力: {paragraph_text}")
    
    paragraphs = re.split(PATENT_PARAGRAPH_PATTERN, paragraph_text)
    paragraph_numbers = re.findall(PATENT_PARAGRAPH_PATTERN, paragraph_text)
    
    print(f"段落番号: {paragraph_numbers}")
    print(f"段落内容: {paragraphs}")
    
    # 再構築テスト
    print(f"\n🔧 再構築テスト:")
    reconstructed = ""
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue
        paragraph_num = paragraph_numbers[i-1] if i > 0 and i-1 < len(paragraph_numbers) else ""
        reconstructed += paragraph_num + paragraph.strip() + " "
    
    print(f"再構築: {reconstructed}")
    
    # セクション名テスト
    section_text = "【発明を実施する形態】実施形態の説明【背景技術】従来技術【0010】段落番号は除外されるべき"
    print(f"\n📑 セクション名テスト:")
    print(f"入力: {section_text}")
    
    section_matches = re.findall(PATENT_SECTION_PATTERN, section_text)
    print(f"セクション名マッチ: {section_matches}")
    print(f"期待結果: ['【発明を実施する形態】', '【背景技術】'] (【0010】は除外)")
    
    # 請求項パターン
    claims_text = "【請求項1】第一の請求項【請求項2】第二の請求項【請求項10】第十の請求項"
    claims_pattern = r'【請求項\d+】'
    print(f"\n⚖️ 請求項パターンテスト:")
    print(f"入力: {claims_text}")
    
    claims_matches = re.findall(claims_pattern, claims_text)
    claims_parts = re.split(claims_pattern, claims_text)
    
    print(f"請求項番号: {claims_matches}")
    print(f"請求項内容: {claims_parts}")

if __name__ == "__main__":
    test_patent_patterns()