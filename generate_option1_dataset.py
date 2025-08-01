#!/usr/bin/env python3
"""Option 1: 段落単位データセット生成"""

import json
import re
from pathlib import Path
from datetime import datetime

def split_into_paragraphs(text):
    """段落番号【XXXX】でテキストを分割"""
    if not text:
        return []
    
    # 段落番号パターンで分割
    paragraphs = re.split(r'(【\d{4}】)', text)
    
    result = []
    current_paragraph = None
    current_number = None
    
    for part in paragraphs:
        if re.match(r'【\d{4}】', part):
            # 前の段落を保存
            if current_number and current_paragraph:
                result.append({
                    'number': current_number,
                    'content': current_paragraph.strip()
                })
            
            # 新しい段落番号
            current_number = part
            current_paragraph = ""
        else:
            # 段落内容
            if current_number:
                current_paragraph += part
    
    # 最後の段落を保存
    if current_number and current_paragraph:
        result.append({
            'number': current_number,
            'content': current_paragraph.strip()
        })
    
    return result

def create_option1_dataset(input_file, output_file, max_items=50):
    """Option 1: 段落単位データセット生成"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 最初の50件のみ処理（テスト用）
    original_data = original_data[:max_items]
    
    option1_data = []
    total_paragraphs = 0
    
    for item in original_data:
        patent_id = item['metadata']['patent_id']
        claims_count = item['metadata']['claims_count']
        
        # userとassistantメッセージを取得
        user_content = None
        assistant_content = None
        
        for msg in item['messages']:
            if msg['role'] == 'user':
                user_content = msg['content']
            elif msg['role'] == 'assistant':
                assistant_content = msg['content']
        
        if not user_content or not assistant_content:
            continue
        
        # 請求項部分を抽出
        claims_text = user_content.replace("以下の特許請求の範囲に基づいて、発明を実施するための形態を説明してください：\n\n", "")
        
        # assistant contentから段落を分割
        # 【発明を実施するための形態】を除去
        implementation_text = assistant_content.replace("【発明を実施するための形態】\n\n", "")
        
        paragraphs = split_into_paragraphs(implementation_text)
        
        if not paragraphs:
            continue
        
        # 各段落を個別のChatMLペアに変換
        for i, paragraph in enumerate(paragraphs):
            # コンテキスト情報
            context_info = f"特許番号: {patent_id}"
            if i > 0:
                # 前の段落の情報を含める
                prev_paragraphs = paragraphs[:i]
                prev_context = "\n".join([f"{p['number']}\n{p['content'][:100]}..." for p in prev_paragraphs])
                context_info += f"\n\n前の段落:\n{prev_context}"
            
            paragraph_record = {
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたは特許文書の専門家です。与えられた特許請求の範囲と文脈に基づいて、指定された段落番号の実施形態を生成してください。"
                    },
                    {
                        "role": "user",
                        "content": f"{context_info}\n\n【請求項】\n{claims_text}\n\n上記に基づいて{paragraph['number']}の段落を生成してください。"
                    },
                    {
                        "role": "assistant",
                        "content": f"{paragraph['number']}\n{paragraph['content']}"
                    }
                ],
                "metadata": {
                    "patent_id": patent_id,
                    "paragraph_number": paragraph['number'],
                    "paragraph_index": i,
                    "total_paragraphs": len(paragraphs),
                    "claims_count": claims_count,
                    "dataset_type": "option1_paragraph_unit",
                    "created_at": datetime.now().isoformat()
                }
            }
            
            option1_data.append(paragraph_record)
            total_paragraphs += 1
    
    # JSON出力
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(option1_data, f, ensure_ascii=False, indent=2)
    
    return len(option1_data), total_paragraphs

# メイン処理
input_file = "/mnt/d/20250728/01tuning/data/processed/chatml_training_with_paragraphs_full.json"
output_file = "/mnt/d/20250728/01tuning/data/processed/option1_paragraph_unit.json"

print("Option 1: 段落単位データセット生成")
print("=" * 80)
print(f"入力ファイル: {Path(input_file).name}")

if not Path(input_file).exists():
    print("❌ 入力ファイルが見つかりません")
    exit(1)

dataset_count, paragraph_count = create_option1_dataset(input_file, output_file)

print(f"✅ Option 1データセット生成完了")
print(f"  出力ファイル: {Path(output_file).name}")
print(f"  生成データ数: {dataset_count}件")
print(f"  総段落数: {paragraph_count}段落")

# サンプル確認
with open(output_file, 'r', encoding='utf-8') as f:
    sample_data = json.load(f)

if sample_data:
    first_sample = sample_data[0]
    print(f"\n📋 サンプル確認:")
    print(f"  特許ID: {first_sample['metadata']['patent_id']}")
    print(f"  段落番号: {first_sample['metadata']['paragraph_number']}")
    print(f"  段落インデックス: {first_sample['metadata']['paragraph_index']}/{first_sample['metadata']['total_paragraphs']-1}")
    
    # userとassistantの内容を表示
    for msg in first_sample['messages']:
        if msg['role'] == 'user':
            print(f"  User (最初の150文字): {msg['content'][:150]}...")
        elif msg['role'] == 'assistant':
            print(f"  Assistant: {msg['content'][:100]}...")

print(f"\n💡 特徴:")
print(f"  - 各段落が独立したChatMLペア")
print(f"  - 前の段落の文脈情報を含む")
print(f"  - 段落番号を明示的に指定")
print(f"  - インタラクティブな段落生成に最適")