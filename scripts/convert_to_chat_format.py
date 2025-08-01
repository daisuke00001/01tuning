#!/usr/bin/env python3
"""
特許データをTinySwallow-1.5B-Instruct用のchat template形式に変換
請求項 → user、実施形態 → assistant の対話形式に変換
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== 定数定義 =====
# セクション検索の優先順位
CLAIMS_SECTIONS = ['claims', 'claim']  # 請求項セクション（厳密）
EMBODIMENT_SECTIONS = ['detailed_description', 'embodiment']  # 実施形態セクション（厳密）

# テキスト長制限
MAX_CLAIMS_LENGTH = 500      # 請求項の最大文字数
MAX_EMBODIMENT_LENGTH = 800  # 実施形態の最大文字数
MIN_CLAIMS_LENGTH = 30       # 請求項の最小文字数  
MIN_EMBODIMENT_LENGTH = 100  # 実施形態の最小文字数

# システムプロンプト
SYSTEM_PROMPT = """あなたは特許の専門家です。請求項から具体的な実施形態を説明してください。"""

# 特許文書マーカーのパターン
PATENT_MARKER_PATTERN = r'【[^】]*】'  # 【課題】【解決手段】等の一般マーカー
PATENT_PARAGRAPH_PATTERN = r'【\d{4}】'  # 【0010】【0011】等の段落番号
PATENT_SECTION_PATTERN = r'【[^】\d][^】]*】'  # 【発明を実施する形態】等のセクション名（数字以外で始まる）
PATENT_ALL_PATTERN = r'【[^】]*】'  # 全ての【】パターン（統合）

class PatentChatFormatter:
    """特許データをchat形式に変換するクラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.cleaned_dir = self.project_root / "data" / "cleaned"
        self.chat_dir = self.project_root / "data" / "chat_format"
        
        # 出力ディレクトリを作成
        self.chat_dir.mkdir(exist_ok=True)
        
    def extract_claims_and_implementations(self, data: List[Dict]) -> List[Dict]:
        """
        特許データから請求項と実施形態のペアを抽出
        
        ロジック詳細:
        1. patent_idごとにセクションをグループ化
        2. 請求項セクションを厳密に検索: claims > claim （abstractは除外）
        3. 実施形態セクションを厳密に検索: detailed_description > embodiment （他は除外）
        4. 両方が存在し、かつ最低文字数を満たす場合のみペア作成
        5. 請求項→実施形態の生成に必要なセクションのみを使用
        """
        
        # patent_idごとにグループ化
        patents_by_id = {}
        for item in data:
            patent_id = item.get('patent_id', 'unknown')
            if patent_id not in patents_by_id:
                patents_by_id[patent_id] = {}
            
            section = item.get('section', 'unknown')
            text = item.get('text', '')
            
            patents_by_id[patent_id][section] = text
        
        logger.info(f"グループ化完了: {len(patents_by_id)}件の特許")
        
        # 請求項と実施形態のペアを作成
        chat_pairs = []
        skipped_stats = {
            'no_claims': 0,
            'no_implementation': 0, 
            'too_short': 0,
            'success': 0
        }
        
        for patent_id, sections in patents_by_id.items():
            # 利用可能なセクションをチェック
            available_sections = list(sections.keys())
            logger.debug(f"Patent {patent_id}: {available_sections}")
            
            # 請求項セクションを厳密に検索（定数使用）
            claims_section = None
            claims_text = ""
            
            for section_name in CLAIMS_SECTIONS:
                if section_name in sections and sections[section_name].strip():
                    claims_section = section_name
                    claims_text = sections[section_name]
                    logger.debug(f"請求項セクション採用: {patent_id} - {section_name}")
                    break
            
            # 実施形態セクションを厳密に検索（定数使用）
            implementation_section = None
            implementation_text = ""
            
            for section_name in EMBODIMENT_SECTIONS:
                if section_name in sections and sections[section_name].strip():
                    implementation_section = section_name
                    implementation_text = sections[section_name]
                    logger.debug(f"実施形態セクション採用: {patent_id} - {section_name}")
                    break
            
            # ペア作成の判定
            if not claims_text:
                skipped_stats['no_claims'] += 1
                logger.debug(f"請求項なしでスキップ: {patent_id}")
                continue
                
            if not implementation_text:
                skipped_stats['no_implementation'] += 1  
                logger.debug(f"実施形態なしでスキップ: {patent_id}")
                continue
            
            # テキストの前処理（文字数制限対応）
            claims_text = self.preprocess_claims(claims_text)
            implementation_text = self.preprocess_implementation(implementation_text)
            
            # 最低長チェック（前処理後、定数使用）
            if len(claims_text) >= MIN_CLAIMS_LENGTH and len(implementation_text) >= MIN_EMBODIMENT_LENGTH:
                chat_pairs.append({
                    'patent_id': patent_id,
                    'claims_section': claims_section,
                    'implementation_section': implementation_section,
                    'user_message': claims_text,
                    'assistant_message': implementation_text
                })
                skipped_stats['success'] += 1
                logger.debug(f"ペア作成成功: {patent_id}")
            else:
                skipped_stats['too_short'] += 1
                logger.debug(f"テキスト長不足でスキップ: {patent_id} (claims:{len(claims_text)}, impl:{len(implementation_text)})")
        
        # 統計情報を出力
        logger.info(f"ペア作成統計:")
        logger.info(f"  - 成功: {skipped_stats['success']}")
        logger.info(f"  - 請求項なし: {skipped_stats['no_claims']}")
        logger.info(f"  - 実施形態なし: {skipped_stats['no_implementation']}")
        logger.info(f"  - 文字数不足: {skipped_stats['too_short']}")
        logger.info(f"抽出されたペア数: {len(chat_pairs)}")
        return chat_pairs
    
    def preprocess_claims(self, text: str) -> str:
        """
        請求項テキストの前処理
        
        特許文書の実際の構造に対応:
        1. 【請求項1】【請求項2】等で区切られる
        2. 各請求項単位で処理
        3. 請求項単位で適切な長さに制限
        """
        if not text:
            return ""
        
        # 余分な空白を除去
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # 文字数制限（定数使用）
        if len(text) <= MAX_CLAIMS_LENGTH:
            return text
        
        # 【請求項1】【請求項2】等で分割
        claims_pattern = r'【請求項\d+】'
        claims_blocks = re.split(claims_pattern, text)
        claims_markers = re.findall(claims_pattern, text)
        
        result = ""
        
        # 各請求項を順次追加
        for i, block in enumerate(claims_blocks):
            if not block.strip():
                continue
                
            # 請求項番号がある場合は追加
            claim_marker = claims_markers[i-1] if i > 0 and i-1 < len(claims_markers) else ""
            potential_claim = claim_marker + block.strip()
            potential_result = result + potential_claim
            
            if len(potential_result) <= MAX_CLAIMS_LENGTH:
                result = potential_result
            else:
                # 現在の結果が空でない場合はそれを使用
                if result:
                    break
                # 結果が空の場合は最初の請求項だけでも強制的に含める
                else:
                    result = potential_claim[:MAX_CLAIMS_LENGTH-3] + '...'
                    break
        
        # まだ結果が空の場合（安全策: 請求項パターンで分割できない場合）
        if not result:
            # 一般的な【****】パターンで分割を試行
            general_blocks = re.split(PATENT_ALL_PATTERN, text)
            general_markers = re.findall(PATENT_ALL_PATTERN, text)
            
            for i, block in enumerate(general_blocks):
                if not block.strip():
                    continue
                    
                marker = general_markers[i-1] if i > 0 and i-1 < len(general_markers) else ""
                potential_block = marker + block.strip()
                
                if len(potential_block) <= MAX_CLAIMS_LENGTH:
                    result = potential_block
                    break
                else:
                    result = potential_block[:MAX_CLAIMS_LENGTH-3] + '...'
                    break
        
        # 最終安全策
        if not result:
            result = text[:MAX_CLAIMS_LENGTH-3] + '...'
        
        logger.debug(f"請求項前処理: {len(text)} → {len(result)} 文字")
        return result
    
    def preprocess_implementation(self, text: str) -> str:
        """
        実施形態テキストの前処理
        
        特許文書の実際の構造に対応:
        1. 【発明を実施する形態】セクションから開始
        2. 【0010】【0011】等の段落番号で区切られる
        3. 段落単位で適切な長さに制限
        """
        if not text:
            return ""
        
        # 余分な空白を除去
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # 文字数制限（定数使用）
        if len(text) <= MAX_EMBODIMENT_LENGTH:
            return text
        
        # 【発明を実施する形態】セクションを検出
        embodiment_start = re.search(r'【発明を実施する形態】', text)
        if embodiment_start:
            # セクション開始位置から処理
            text = text[embodiment_start.start():]
            
        # 段落番号【0010】【0011】等で分割
        paragraphs = re.split(PATENT_PARAGRAPH_PATTERN, text)
        paragraph_numbers = re.findall(PATENT_PARAGRAPH_PATTERN, text)
        
        result = ""
        
        # 各段落を順次追加
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            # 段落番号がある場合は追加
            paragraph_num = paragraph_numbers[i-1] if i > 0 and i-1 < len(paragraph_numbers) else ""
            
            # 最初の段落の場合、【発明を実施する形態】を含める可能性
            if i == 0 and '【発明を実施する形態】' in paragraph:
                potential_paragraph = paragraph.strip()
            else:
                potential_paragraph = paragraph_num + paragraph.strip()
                
            potential_result = result + potential_paragraph
            
            if len(potential_result) <= MAX_EMBODIMENT_LENGTH:
                result = potential_result
            else:
                # 現在の結果が空でない場合はそれを使用
                if result:
                    break
                # 結果が空の場合は最初の段落だけでも強制的に含める
                else:
                    result = potential_paragraph[:MAX_EMBODIMENT_LENGTH-3] + '...'
                    break
        
        # まだ結果が空の場合（安全策: 段落番号パターンで分割できない場合）
        if not result:
            # セクション名【****】で分割を試行
            section_blocks = re.split(PATENT_SECTION_PATTERN, text)
            section_markers = re.findall(PATENT_SECTION_PATTERN, text)
            
            for i, block in enumerate(section_blocks):
                if not block.strip():
                    continue
                    
                marker = section_markers[i-1] if i > 0 and i-1 < len(section_markers) else ""
                potential_block = marker + block.strip()
                
                if len(potential_block) <= MAX_EMBODIMENT_LENGTH:
                    result = potential_block
                    break
                else:
                    result = potential_block[:MAX_EMBODIMENT_LENGTH-3] + '...'
                    break
        
        # 最終安全策
        if not result:
            result = text[:MAX_EMBODIMENT_LENGTH-3] + '...'
        
        logger.debug(f"実施形態前処理: {len(text)} → {len(result)} 文字")
        return result
    
    def create_chat_template(self, user_message: str, assistant_message: str) -> str:
        """Chat template形式を作成（定数使用）"""
        
        # TinySwallow-1.5B-Instruct用のchat template
        chat_template = f"""<|im_start|>system
{SYSTEM_PROMPT}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_message}<|im_end|>"""
        
        return chat_template
    
    def convert_to_chat_format(self, input_file: str, output_file: str):
        """メイン変換処理"""
        
        input_path = self.cleaned_dir / input_file
        output_path = self.chat_dir / output_file
        
        logger.info(f"変換開始: {input_path} → {output_path}")
        
        # データ読み込み
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"入力データ数: {len(data)}")
        except Exception as e:
            logger.error(f"ファイル読み込みエラー: {e}")
            return
        
        # ペア抽出
        chat_pairs = self.extract_claims_and_implementations(data)
        
        if not chat_pairs:
            logger.error("有効なペアが抽出できませんでした")
            return
        
        # Chat format変換
        chat_dataset = []
        
        for i, pair in enumerate(chat_pairs):
            try:
                chat_text = self.create_chat_template(
                    pair['user_message'],
                    pair['assistant_message']
                )
                
                chat_item = {
                    "text": chat_text,
                    "patent_id": pair['patent_id'],
                    "claims_section": pair['claims_section'],
                    "implementation_section": pair['implementation_section']
                }
                
                chat_dataset.append(chat_item)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"変換進捗: {i + 1}/{len(chat_pairs)}")
                    
            except Exception as e:
                logger.warning(f"ペア {i} の変換でエラー: {e}")
                continue
        
        # 保存
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chat_dataset, f, ensure_ascii=False, indent=2)
            
            logger.info(f"変換完了: {output_path}")
            logger.info(f"出力データ数: {len(chat_dataset)}")
            
            # ファイルサイズ表示
            file_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"ファイルサイズ: {file_size:.2f} MB")
            
            # サンプル表示
            if chat_dataset:
                sample = chat_dataset[0]
                logger.info("📊 サンプルチャット:")
                logger.info(f"テキスト長: {len(sample['text'])}")
                logger.info(f"プレビュー:\n{sample['text'][:300]}...")
                
        except Exception as e:
            logger.error(f"保存エラー: {e}")
    
    def run_conversion(self):
        """メイン実行処理"""
        logger.info("=" * 60)
        logger.info("Chat Format変換開始")
        logger.info("=" * 60)
        
        # 利用可能なファイルを確認
        json_files = list(self.cleaned_dir.glob("cleaned_*.json"))
        
        if not json_files:
            logger.error(f"クリーニング済みファイルが見つかりません: {self.cleaned_dir}")
            return
        
        logger.info(f"見つかったファイル: {len(json_files)}")
        for file_path in json_files:
            logger.info(f"  - {file_path.name}")
        
        # 各ファイルを変換
        conversions = [
            ("cleaned_patents_small.json", "chat_patents_small.json"),
            ("cleaned_patents_medium.json", "chat_patents_medium.json"),
            ("cleaned_training_dataset.json", "chat_training_dataset.json"),
        ]
        
        for input_file, output_file in conversions:
            input_path = self.cleaned_dir / input_file
            if input_path.exists():
                self.convert_to_chat_format(input_file, output_file)
            else:
                logger.warning(f"ファイルが存在しません: {input_file}")
        
        logger.info("=" * 60)
        logger.info("Chat Format変換完了")
        logger.info("=" * 60)


def main():
    """メイン実行関数"""
    formatter = PatentChatFormatter()
    formatter.run_conversion()

if __name__ == "__main__":
    main()