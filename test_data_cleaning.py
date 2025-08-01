# 🧪 データクリーニングテスト用コード
import json
import re
import os

def test_data_cleaning():
    """サンプルデータでクリーニング機能をテスト"""
    
    # サンプルデータ（提供されたデータから抜粋）
    sample_data = {
        "patent_id": "7620367",
        "title": "精神障害分析装置",
        "text": "精神障害分析装置 課題精神障害であることを分析する精神障害分析装置を提供する。解決手段精神障害分析装置は、精神障害であると診断された患者CHCHCHCHCHCHEMICAL6479MICCHEMICACHEMICACHEMICAL647864626461L6459MICACHEMICACHEMICACHEMICAL6458645364386434MICACHEMICAL64336424MICACHEMICAL64236414MICAL6413ECHEMICAL6415AL20学習用動画を教師データとして学習させた精神障害学習モデルを記憶させる記憶部と、分析対象者LECHEMICAL6460AL21分析対象動画を取得する取得部と、分析対象動画に精神障害学習モデルを適用して、分析対象者が精神障害であるか否かを分析する分析部と、LECHEMICAL6480AL00。"
    }
    
    print("🔍 データクリーニングテスト開始")
    print("=" * 60)
    
    # 元のテキスト情報
    original_text = sample_data["text"]
    print(f"📊 元データ:")
    print(f"  - 文字数: {len(original_text):,}")
    print(f"  - プレビュー: {original_text[:200]}...")
    
    # クリーニング関数
    def clean_patent_text(text: str) -> str:
        """特許テキストのクリーニング"""
        if not isinstance(text, str):
            return ""
        
        # 異常な文字列パターンを除去
        text = re.sub(r'CHEMICAL\d+', '', text)
        text = re.sub(r'LEGAL\d+', '', text)
        text = re.sub(r'MIC[A-Z]*', '', text)
        text = re.sub(r'CH{3,}', '', text)
        text = re.sub(r'AL\d+', '', text)
        text = re.sub(r'LE[A-Z]*', '', text)
        
        # 連続する同じ文字を除去
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        # 複数の空白を単一に
        text = re.sub(r'\s+', ' ', text)
        
        # 制御文字を除去
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def limit_text_length(text: str, max_length: int = 1000) -> str:
        """テキスト長を制限"""
        if len(text) > max_length:
            sentences = text.split('。')
            result = ""
            for sentence in sentences:
                if len(result + sentence + '。') <= max_length:
                    result += sentence + '。'
                else:
                    break
            return result if result else text[:max_length]
        return text
    
    # クリーニング実行
    cleaned_text = clean_patent_text(original_text)
    limited_text = limit_text_length(cleaned_text, 800)
    
    print(f"\n✅ クリーニング後:")
    print(f"  - 文字数: {len(limited_text):,}")
    print(f"  - 短縮率: {(1 - len(limited_text)/len(original_text))*100:.1f}%")
    print(f"  - プレビュー: {limited_text[:300]}...")
    
    # 学習用データセット作成
    clean_dataset = [{
        "text": limited_text,
        "patent_id": sample_data["patent_id"],
        "title": sample_data["title"]
    }]
    
    return clean_dataset

# テスト実行
test_dataset = test_data_cleaning()

# HuggingFace Datasetsに変換してテスト
from datasets import Dataset
dataset = Dataset.from_list(test_dataset)

print(f"\n🎯 データセット作成完了:")
print(f"  - データ数: {len(dataset)}")
print(f"  - キー: {list(dataset[0].keys())}")
print(f"  - テキスト長: {len(dataset[0]['text'])}")

print("\n✅ データクリーニングテスト完了")
print("💡 このクリーニング済みデータで学習をテストできます")