#!/usr/bin/env python3
"""Option 2: 会話履歴形式データセット生成"""

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

def create_option2_dataset(input_file, output_file, max_items=50):
    """Option 2: 会話履歴形式データセット生成"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 最初の50件のみ処理（テスト用）
    original_data = original_data[:max_items]
    
    option2_data = []
    total_conversations = 0
    total_turns = 0
    
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
        
        if len(paragraphs) < 2:  # 最低2段落必要
            continue
        
        # 会話履歴形式に変換
        messages = [
            {
                "role": "system",
                "content": "あなたは特許文書の専門家です。ユーザーの請求項に基づいて、実施形態を段落ごとに対話形式で生成してください。ユーザーが「次へ」と言ったら次の段落を生成してください。"
            },
            {
                "role": "user", 
                "content": f"以下の特許請求の範囲に基づいて、実施形態を段落ごとに生成してください：\n\n{claims_text}\n\n最初の段落からお願いします。"
            },
            # 最初の段落
            {
                "role": "assistant",
                "content": f"{paragraphs[0]['number']}\n{paragraphs[0]['content']}"
            }
        ]
        
        # 残りの段落を会話として追加
        for i in range(1, len(paragraphs)):
            # ユーザーリクエスト
            if i == len(paragraphs) - 1:
                user_request = "最後の段落をお願いします。"
            else:
                user_request = "次の段落をお願いします。"
            
            messages.append({
                "role": "user",
                "content": user_request
            })
            
            # AIレスポンス
            messages.append({
                "role": "assistant", 
                "content": f"{paragraphs[i]['number']}\n{paragraphs[i]['content']}"
            })
        
        conversation_record = {
            "messages": messages,
            "metadata": {
                "patent_id": patent_id,
                "total_paragraphs": len(paragraphs),
                "conversation_turns": len(messages),
                "claims_count": claims_count,
                "dataset_type": "option2_conversation",
                "created_at": datetime.now().isoformat()
            }
        }
        
        option2_data.append(conversation_record)
        total_conversations += 1
        total_turns += len(messages)
    
    # JSON出力
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(option2_data, f, ensure_ascii=False, indent=2)
    
    return len(option2_data), total_turns

# メイン処理
input_file = "/mnt/d/20250728/01tuning/data/processed/chatml_training_with_paragraphs_full.json"
output_file = "/mnt/d/20250728/01tuning/data/processed/option2_conversation.json"

print("Option 2: 会話履歴形式データセット生成")
print("=" * 80)
print(f"入力ファイル: {Path(input_file).name}")

if not Path(input_file).exists():
    print("❌ 入力ファイルが見つかりません")
    exit(1)

dataset_count, turn_count = create_option2_dataset(input_file, output_file)

print(f"✅ Option 2データセット生成完了")
print(f"  出力ファイル: {Path(output_file).name}")
print(f"  生成会話数: {dataset_count}件")
print(f"  総ターン数: {turn_count}ターン")

# サンプル確認
with open(output_file, 'r', encoding='utf-8') as f:
    sample_data = json.load(f)

if sample_data:
    first_sample = sample_data[0]
    print(f"\n📋 サンプル確認:")
    print(f"  特許ID: {first_sample['metadata']['patent_id']}")
    print(f"  段落数: {first_sample['metadata']['total_paragraphs']}")
    print(f"  会話ターン数: {first_sample['metadata']['conversation_turns']}")
    
    # 会話の最初の3ターンを表示
    messages = first_sample['messages'][:6]  # system + 最初の5ターン
    for i, msg in enumerate(messages):
        role = msg['role']
        content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"  Turn {i} ({role}): {content}")

print(f"\n💡 特徴:")
print(f"  - 多ターン会話形式")
print(f"  - 段階的な段落生成を学習")
print(f"  - 「次へ」コマンドの理解")
print(f"  - 自然な対話フローを重視")