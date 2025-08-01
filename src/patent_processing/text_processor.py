"""
特許文書のテキスト前処理を行うモジュール
日本特許庁のST96 XMLフォーマットに対応
"""

import re
import pandas as pd
import xml.etree.ElementTree as ET
import json
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Tuple, Mapping
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# ロガーの初期化
logger = logging.getLogger(__name__)


class PatentTextProcessor:
    """特許文書のテキスト前処理クラス"""
    
    def __init__(self, language: str = "japanese", enable_chemical_processing: bool = True,
                 max_description_length: Optional[int] = None,
                 description_sources: Optional[List[str]] = None):
        """
        初期化
        
        Args:
            language: 処理対象の言語 ('japanese' or 'english')
            enable_chemical_processing: 化学式処理を有効にするかどうか
            max_description_length: 実施形態説明の最大文字数（Noneの場合は制限なし）
            description_sources: 使用する説明タグのリスト（Noneの場合は全て使用）
                                ['EmbodimentDescription', 'DetailedDescription', 'BestMode', 'InventionMode']
        """
        self.language = language
        self.enable_chemical_processing = enable_chemical_processing
        self.max_description_length = max_description_length or 50000  # デフォルト50,000文字
        self.description_sources = description_sources or [
            'EmbodimentDescription', 'DetailedDescription', 'BestMode', 'InventionMode'
        ]
        self._download_nltk_data()
        
        # 化学式処理の初期化
        if self.enable_chemical_processing:
            self._init_chemical_patterns()
            
        # 法的表現保持の初期化
        self._init_legal_expressions()
        
        # ST96 XMLフォーマットの名前空間定義
        self.namespaces = {
            'jppat': 'http://www.jpo.go.jp/standards/XMLSchema/ST96/JPPatent',
            'jpcom': 'http://www.jpo.go.jp/standards/XMLSchema/ST96/JPCommon',
            'com': 'http://www.wipo.int/standards/XMLSchema/ST96/Common',
            'pat': 'http://www.wipo.int/standards/XMLSchema/ST96/Patent'
        }
        
    def _download_nltk_data(self):
        """必要なNLTKデータをダウンロード"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
    
    def _init_chemical_patterns(self):
        """化学式処理用のパターンを初期化"""
        # 有機化合物の分子式（C07分野中心）
        self.organic_molecular_formulas = [
            r'C\d{1,3}H\d{1,3}(?:O\d{1,2})?(?:N\d{1,2})?(?:S\d{1,2})?(?:P\d{1,2})?(?:Cl\d{1,2})?(?:Br\d{1,2})?(?:F\d{1,2})?(?:I\d{1,2})?',
            r'(?:CH₃|CH₂|CH|C)(?:[-–](?:CH₃|CH₂|CH|C))*',  # 構造式表記
            r'R₁|R₂|R₃|R₄|X|Y|Z',  # 化学式中の置換基表記
        ]
        
        # 無機化合物（C01分野中心）
        self.inorganic_compounds = [
            r'H₂SO₄|HCl|HNO₃|H₃PO₄|NH₃|NaOH|KOH|Ca\(OH\)₂',  # 主要酸・塩基
            r'NaCl|KCl|CaCl₂|MgSO₄|Na₂CO₃|K₂CO₃|NaHCO₃',  # 主要塩類
            r'TiO₂|SiO₂|Al₂O₃|Fe₂O₃|CuO|ZnO|MgO|CaO',  # 金属酸化物
            r'[A-Z][a-z]?(?:\d+)?(?:[+-]\d*)?',  # 元素記号＋イオン
        ]
        
        # 高分子化合物（C08分野）
        self.polymer_formulas = [
            r'\[-(?:CH₂[-–]CH₂[-–]|CH₂[-–]CHR[-–]|CH₂[-–]CR₂[-–])+\]ₙ',  # ポリマー表記
            r'(?:PE|PP|PS|PVC|PET|PMMA|PA|PC|PU|PTFE)',  # 高分子略号
            r'Mw\s*[=:]\s*\d+(?:[,，]\d+)*|Mn\s*[=:]\s*\d+(?:[,，]\d+)*',  # 分子量
            r'重合度\s*[=:]\s*\d+(?:[,，]\d+)*',
        ]
        
        # 化学反応式
        self.chemical_reactions = [
            r'[A-Z][a-z]?\d*(?:\s*[+＋]\s*[A-Z][a-z]?\d*)*\s*[→⇒]\s*[A-Z][a-z]?\d*(?:\s*[+＋]\s*[A-Z][a-z]?\d*)*',
            r'[A-Z][a-z]?\d*\s*[⇌⇔]\s*[A-Z][a-z]?\d*',  # 平衡反応
            r'[A-Z][a-z]?\d*\s*[→⇒]\s*[A-Z][a-z]?\d*\s*/\s*[A-Z][a-z]?',  # 触媒反応
        ]
        
        # 化学的性質・数値
        self.chemical_properties = [
            r'融点\s*[=:：]?\s*\d+(?:\.\d+)?(?:[～〜~]\d+(?:\.\d+)?)?\s*℃',
            r'沸点\s*[=:：]?\s*\d+(?:\.\d+)?(?:[～〜~]\d+(?:\.\d+)?)?\s*℃',
            r'\d+(?:\.\d+)?\s*(?:wt%|重量%|質量%|mol%|体積%|重量％|質量％|体積％)',
            r'純度\s*[=:：]?\s*\d+(?:\.\d+)?\s*%以上',
            r'pH\s*[=:：]?\s*\d+(?:\.\d+)?(?:[～〜~]\d+(?:\.\d+)?)?',
            r'pKa\s*[=:：]?\s*\d+(?:\.\d+)?',
            r'収率\s*[=:：]?\s*\d+(?:\.\d+)?\s*%',
            r'選択性\s*[=:：]?\s*\d+(?:\.\d+)?\s*%',
        ]
        
        # 実験条件・装置
        self.experimental_conditions = [
            r'\d+(?:\.\d+)?\s*℃(?:で|にて|において|に|下で)',
            r'\d+(?:\.\d+)?\s*(?:MPa|kPa|mmHg|Torr|Pa|atm)(?:で|にて|において|に|下で)',
            r'\d+(?:\.\d+)?\s*(?:時間|分|秒|hr|min|sec)(?:反応させ|加熱し|撹拌し|処理し)',
            r'(?:オートクレーブ|反応器|蒸留塔|分離塔|カラム|反応釜)(?:中で|内で|にて)',
        ]
        
        # 全パターンをまとめる
        self.all_chemical_patterns = (
            self.organic_molecular_formulas + 
            self.inorganic_compounds + 
            self.polymer_formulas + 
            self.chemical_reactions + 
            self.chemical_properties + 
            self.experimental_conditions
        )
        
        # コンパイル済み正規表現パターンを作成
        self.compiled_chemical_patterns = [re.compile(pattern) for pattern in self.all_chemical_patterns]
        
        # 化学コンテキストキーワード
        self.chemical_context_keywords = [
            '化合物', '分子', '溶液', '反応', '合成', '製造', '調製', '精製',
            '結晶', '溶媒', '触媒', '重合', '酸化', '還元', '加水分解',
            '濃度', '純度', '収率', '選択性', 'モル', '当量', '組成',
            '原料', '試薬', '生成物', '副生成物', '中間体', '最終産物'
        ]
        
        # 非化学コンテキストキーワード（偽陽性を防ぐ）
        self.non_chemical_context_keywords = [
            '年度', '削減', '問題', '項目', '番号', '章', '条', '節',
            '図', '表', '例', 'データ', 'システム', 'プログラム',
            'コード', 'ファイル', 'バージョン', 'モデル'
        ]
    
    def _init_legal_expressions(self):
        """特許法的表現の初期化"""
        # 請求項における重要な法的表現
        self.claim_legal_expressions = [
            # 構成要素の記述
            r'を備える(?:こと)?',
            r'を有する(?:こと)?',
            r'を含む(?:こと)?',
            r'を含有する(?:こと)?',
            r'からなる(?:こと)?',
            r'から構成される(?:こと)?',
            
            # 依存関係・参照表現
            r'前記[^。、]*',
            r'上記[^。、]*',
            r'該[^。、]*',
            r'当該[^。、]*',
            
            # 特許特有の修飾表現
            r'所定の[^。、]*',
            r'少なくとも[^。、]*',
            r'一つ以上の[^。、]*',
            r'複数の[^。、]*',
            
            # 権利範囲の限定
            r'であって[^。、]*',
            r'において[^。、]*',
            r'による[^。、]*',
            r'に関する[^。、]*',
            r'に係る[^。、]*',
            
            # 特徴表現
            r'ことを特徴とする[^。、]*',
            r'ことを要旨とする[^。、]*',
            r'を特徴とする[^。、]*',
        ]
        
        # 明細書における法的表現
        self.description_legal_expressions = [
            # 発明の効果・作用
            r'効果を奏する',
            r'作用を生じる',
            r'機能を発揮する',
            r'性能を向上させる',
            
            # 実施形態の表現
            r'実施の形態',
            r'実施例',
            r'具体例',
            r'変形例',
            r'応用例',
            
            # 技術的効果の表現
            r'改善される',
            r'向上する',
            r'防止される',
            r'解決される',
            r'達成される',
            
            # 課題・問題の表現
            r'課題を解決する',
            r'問題を克服する',
            r'欠点を補う',
            r'不具合を改善する',
        ]
        
        # 手続的表現
        self.procedural_expressions = [
            # 工程・手順
            r'工程を含む',
            r'手順により',
            r'方法によって',
            r'プロセスにより',
            
            # 条件・状態
            r'条件下で',
            r'状態において',
            r'環境で',
            r'状況で',
            
            # 手段・方法
            r'手段により',
            r'方法を用いて',
            r'技術によって',
            r'システムを使用して',
        ]
        
        # 全ての法的表現パターンをまとめる
        self.all_legal_patterns = (
            self.claim_legal_expressions +
            self.description_legal_expressions +
            self.procedural_expressions
        )
        
        # コンパイル済み正規表現
        self.compiled_legal_patterns = [re.compile(pattern) for pattern in self.all_legal_patterns]
        
        # 重要度による分類
        self.critical_legal_expressions = [
            'ことを特徴とする', 'を備える', 'を有する', 'からなる', 
            '前記', '所定の', 'であって', 'において'
        ]
        
        self.important_legal_expressions = [
            'を含む', '少なくとも', '複数の', 'による', 'に関する',
            '実施の形態', '効果を奏する', '課題を解決する'
        ]
    
    def clean_text(self, text: str) -> str:
        """
        テキストの基本的なクリーニング
        
        Args:
            text: 入力テキスト
            
        Returns:
            クリーニング済みテキスト
        """
        if not isinstance(text, str):
            return ""
            
        # 改行と余分な空白の正規化
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # 言語別の文字セット制限
        if self.language == "japanese":
            text = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3400-\u4DBFa-zA-Z0-9\s\.,;:!?()\[\]{}「」『』。、]', '', text)
        else:
            text = re.sub(r'[^a-zA-Z0-9\s\.,;:!?()\[\]{}]', '', text)
            
        return text.strip()
    
    def protect_chemical_formulas(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        化学式・数式を一時的にトークン化して保護
        
        Args:
            text: 入力テキスト
            
        Returns:
            保護されたテキストと化学式マップのタプル
        """
        if not self.enable_chemical_processing:
            return text, {}
            
        protected_text = text
        formula_map = {}
        
        for i, pattern in enumerate(self.compiled_chemical_patterns):
            matches = list(pattern.finditer(protected_text))
            for j, match in enumerate(matches):
                formula = match.group()
                
                # コンテキスト判定
                if self._is_valid_chemical_context(protected_text, match.start(), match.end()):
                    token = f"__CHEMICAL_{i}_{j}__"
                    formula_map[token] = formula
                    protected_text = protected_text.replace(formula, token, 1)
        
        return protected_text, formula_map
    
    def restore_chemical_formulas(self, text: str, formula_map: Dict[str, str]) -> str:
        """
        保護されたトークンを元の化学式・数式に復元
        
        Args:
            text: 保護されたテキスト
            formula_map: 化学式マップ
            
        Returns:
            復元されたテキスト
        """
        for token, formula in formula_map.items():
            text = text.replace(token, formula)
        return text
    
    def _is_valid_chemical_context(self, text: str, start_pos: int, end_pos: int) -> bool:
        """
        化学式が適切なコンテキストにあるかチェック
        
        Args:
            text: 全体のテキスト
            start_pos: マッチ開始位置
            end_pos: マッチ終了位置
            
        Returns:
            化学的コンテキストかどうか
        """
        # 前後20文字のコンテキストを取得
        context_size = 20
        before_context = text[max(0, start_pos - context_size):start_pos]
        after_context = text[end_pos:min(len(text), end_pos + context_size)]
        full_context = before_context + after_context
        
        # 化学的コンテキストキーワードの存在確認
        chemical_score = sum(1 for keyword in self.chemical_context_keywords 
                           if keyword in full_context)
        
        # 非化学的コンテキストキーワードの存在確認
        non_chemical_score = sum(1 for keyword in self.non_chemical_context_keywords 
                               if keyword in full_context)
        
        # 化学的コンテキストが優勢な場合のみTrue
        return chemical_score > non_chemical_score
    
    def extract_chemical_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        テキストから化学エンティティを抽出・分類
        
        Args:
            text: 入力テキスト
            
        Returns:
            化学エンティティのリスト
        """
        if not self.enable_chemical_processing:
            return []
            
        entities = []
        
        pattern_categories = [
            ('organic_molecular', self.organic_molecular_formulas),
            ('inorganic_compound', self.inorganic_compounds),
            ('polymer', self.polymer_formulas),
            ('reaction', self.chemical_reactions),
            ('property', self.chemical_properties),
            ('condition', self.experimental_conditions),
        ]
        
        for category, patterns in pattern_categories:
            for pattern in patterns:
                compiled_pattern = re.compile(pattern)
                for match in compiled_pattern.finditer(text):
                    if self._is_valid_chemical_context(text, match.start(), match.end()):
                        entity = {
                            'text': match.group(),
                            'category': category,
                            'start': match.start(),
                            'end': match.end(),
                            'pattern': pattern
                        }
                        entities.append(entity)
        
        # 重複除去（同じ位置の重複マッチを防ぐ）
        entities = self._remove_overlapping_entities(entities)
        
        return entities
    
    def _remove_overlapping_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複するエンティティを除去"""
        if not entities:
            return []
            
        # 開始位置でソート
        entities.sort(key=lambda x: x['start'])
        
        filtered = [entities[0]]
        
        for entity in entities[1:]:
            # 前のエンティティと重複していない場合のみ追加
            if entity['start'] >= filtered[-1]['end']:
                filtered.append(entity)
        
        return filtered
    
    def enhanced_clean_text(self, text: str) -> str:
        """
        化学式・法的表現保護機能付きの高度テキストクリーニング
        
        Args:
            text: 入力テキスト
            
        Returns:
            クリーニング済みテキスト
        """
        if not isinstance(text, str):
            return ""
        
        # 1. 法的表現の保護
        protected_text, legal_map = self.protect_legal_expressions(text)
        
        # 2. 化学式の保護
        if self.enable_chemical_processing:
            protected_text, formula_map = self.protect_chemical_formulas(protected_text)
        else:
            formula_map = {}
        
        # 3. 基本的なクリーニング
        cleaned_text = self.clean_text(protected_text)
        
        # 4. 化学式の復元
        if formula_map:
            cleaned_text = self.restore_chemical_formulas(cleaned_text, formula_map)
        
        # 5. 法的表現の復元
        final_text = self.restore_legal_expressions(cleaned_text, legal_map)
        
        return final_text
    
    def analyze_chemical_content(self, text: str) -> Dict[str, Any]:
        """
        テキストの化学的内容を詳細分析
        
        Args:
            text: 入力テキスト
            
        Returns:
            化学的内容の分析結果
        """
        if not self.enable_chemical_processing:
            return {'enabled': False}
            
        entities = self.extract_chemical_entities(text)
        
        # カテゴリ別統計
        category_counts = {}
        for entity in entities:
            category = entity['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # ユニークな化学式の抽出
        unique_formulas = list(set(entity['text'] for entity in entities))
        
        # 複雑度スコアの計算
        complexity_score = self._calculate_chemical_complexity(entities)
        
        analysis_result = {
            'enabled': True,
            'total_entities': len(entities),
            'unique_formulas': len(unique_formulas),
            'category_counts': category_counts,
            'complexity_score': complexity_score,
            'entities': entities,
            'unique_formulas_list': unique_formulas
        }
        
        return analysis_result
    
    def _calculate_chemical_complexity(self, entities: List[Dict[str, Any]]) -> float:
        """
        化学的複雑度スコアを計算
        
        Args:
            entities: 化学エンティティのリスト
            
        Returns:
            複雑度スコア（0.0-1.0）
        """
        if not entities:
            return 0.0
        
        complexity_weights = {
            'organic_molecular': 0.3,
            'inorganic_compound': 0.2,
            'polymer': 0.4,
            'reaction': 0.5,
            'property': 0.1,
            'condition': 0.1
        }
        
        total_score = 0.0
        for entity in entities:
            category = entity['category']
            weight = complexity_weights.get(category, 0.1)
            
            # テキスト長による追加重み
            length_factor = min(len(entity['text']) / 20.0, 1.0)
            total_score += weight * (1.0 + length_factor)
        
        # 正規化（最大値で割る）
        max_possible_score = len(entities) * 1.0  # 最大重み値
        normalized_score = min(total_score / max_possible_score, 1.0)
        
        return round(normalized_score, 3)
    
    def protect_legal_expressions(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        法的表現を一時的にトークン化して保護
        
        Args:
            text: 入力テキスト
            
        Returns:
            保護されたテキストと法的表現マップのタプル
        """
        protected_text = text
        legal_map = {}
        
        for i, pattern in enumerate(self.compiled_legal_patterns):
            matches = list(pattern.finditer(protected_text))
            for j, match in enumerate(matches):
                legal_expr = match.group()
                
                # 重要度チェック
                importance = self._get_legal_expression_importance(legal_expr)
                if importance >= 1:  # 重要または重要度クリティカル
                    token = f"__LEGAL_{i}_{j}__"
                    legal_map[token] = {
                        'expression': legal_expr,
                        'importance': importance,
                        'category': self._categorize_legal_expression(legal_expr)
                    }
                    protected_text = protected_text.replace(legal_expr, token, 1)
        
        return protected_text, legal_map
    
    def restore_legal_expressions(self, text: str, legal_map: Mapping[str, Union[str,Dict[str,Any]]]) -> str:
        """
        保護されたトークンを元の法的表現に復元
        
        Args:
            text: 保護されたテキスト
            legal_map: 法的表現マップ
            
        Returns:
            復元されたテキスト
        """
        for token, legal_data in legal_map.items():
            if isinstance(legal_data, dict):
                expression = legal_data.get('expression', '')
            else:
                expression = legal_data
            text = text.replace(token, expression)
        return text
    
    def _get_legal_expression_importance(self, expression: str) -> int:
        """
        法的表現の重要度を判定
        
        Args:
            expression: 法的表現
            
        Returns:
            重要度 (0: 通常, 1: 重要, 2: クリティカル)
        """
        for critical_expr in self.critical_legal_expressions:
            if critical_expr in expression:
                return 2  # クリティカル
        
        for important_expr in self.important_legal_expressions:
            if important_expr in expression:
                return 1  # 重要
        
        return 0  # 通常
    
    def _categorize_legal_expression(self, expression: str) -> str:
        """
        法的表現のカテゴリを判定
        
        Args:
            expression: 法的表現
            
        Returns:
            カテゴリ名
        """
        # 請求項表現のチェック
        for pattern in self.claim_legal_expressions:
            if re.search(pattern, expression):
                return 'claim'
        
        # 明細書表現のチェック
        for pattern in self.description_legal_expressions:
            if re.search(pattern, expression):
                return 'description'
        
        # 手続表現のチェック
        for pattern in self.procedural_expressions:
            if re.search(pattern, expression):
                return 'procedural'
        
        return 'general'
    
    def extract_legal_expressions(self, text: str) -> List[Dict[str, Any]]:
        """
        テキストから法的表現を抽出・分析
        
        Args:
            text: 入力テキスト
            
        Returns:
            法的表現のリスト
        """
        expressions = []
        
        for i, pattern in enumerate(self.compiled_legal_patterns):
            for match in pattern.finditer(text):
                legal_expr = match.group()
                importance = self._get_legal_expression_importance(legal_expr)
                category = self._categorize_legal_expression(legal_expr)
                
                expression_data = {
                    'text': legal_expr,
                    'start': match.start(),
                    'end': match.end(),
                    'importance': importance,
                    'category': category,
                    'pattern_index': i
                }
                expressions.append(expression_data)
        
        # 重複除去（同じ位置の重複マッチを防ぐ）
        expressions = self._remove_overlapping_legal_expressions(expressions)
        
        return expressions
    
    def _remove_overlapping_legal_expressions(self, expressions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複する法的表現を除去（重要度を考慮）"""
        if not expressions:
            return []
        
        # 開始位置でソート
        expressions.sort(key=lambda x: (x['start'], -x['importance']))
        
        filtered = [expressions[0]]
        
        for expr in expressions[1:]:
            # 前の表現と重複していない、または重要度が高い場合
            if (expr['start'] >= filtered[-1]['end'] or 
                expr['importance'] > filtered[-1]['importance']):
                # 重要度が高い場合は前の表現を置き換え
                if (expr['start'] < filtered[-1]['end'] and 
                    expr['importance'] > filtered[-1]['importance']):
                    filtered[-1] = expr
                else:
                    filtered.append(expr)
        
        return filtered
    
    def analyze_legal_content(self, text: str) -> Dict[str, Any]:
        """
        テキストの法的表現内容を詳細分析
        
        Args:
            text: 入力テキスト
            
        Returns:
            法的表現の分析結果
        """
        expressions = self.extract_legal_expressions(text)
        
        # カテゴリ別統計
        category_counts = {}
        importance_counts = {0: 0, 1: 0, 2: 0}
        
        for expr in expressions:
            category = expr['category']
            importance = expr['importance']
            
            category_counts[category] = category_counts.get(category, 0) + 1
            importance_counts[importance] += 1
        
        # 法的品質スコアの計算
        legal_quality_score = self._calculate_legal_quality_score(expressions)
        
        analysis_result = {
            'total_expressions': len(expressions),
            'category_counts': category_counts,
            'importance_distribution': {
                'critical': importance_counts[2],
                'important': importance_counts[1],
                'normal': importance_counts[0]
            },
            'legal_quality_score': legal_quality_score,
            'expressions': expressions,
            'has_claim_expressions': any(expr['category'] == 'claim' for expr in expressions),
            'has_critical_expressions': any(expr['importance'] == 2 for expr in expressions)
        }
        
        return analysis_result
    
    def _calculate_legal_quality_score(self, expressions: List[Dict[str, Any]]) -> float:
        """
        法的表現の品質スコアを計算
        
        Args:
            expressions: 法的表現のリスト
            
        Returns:
            品質スコア（0.0-1.0）
        """
        if not expressions:
            return 0.0
        
        # 重要度による重み付け
        total_score = 0.0
        for expr in expressions:
            importance = expr['importance']
            if importance == 2:  # クリティカル
                total_score += 1.0
            elif importance == 1:  # 重要
                total_score += 0.6
            else:  # 通常
                total_score += 0.3
        
        # カテゴリの多様性ボーナス
        unique_categories = len(set(expr['category'] for expr in expressions))
        diversity_bonus = min(unique_categories * 0.1, 0.3)
        
        # 正規化
        max_possible_score = len(expressions) * 1.0
        normalized_score = min((total_score + diversity_bonus) / max_possible_score, 1.0)
        
        return round(normalized_score, 3)
    
    def validate_patent_data(self, patent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        実務レベルのデータ品質チェック
        
        Args:
            patent_data: 特許データ辞書
            
        Returns:
            検証結果辞書
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'quality_score': 0.0,
            'checks_performed': [],
            'recommendations': []
        }
        
        # 1. 必須フィールドの存在確認
        required_fields = ['patent_number', 'title', 'claims', 'detailed_description']
        missing_fields = [field for field in required_fields if not patent_data.get(field)]
        
        if missing_fields:
            validation_result['errors'].extend([f"必須フィールド '{field}' が存在しません" for field in missing_fields])
            validation_result['is_valid'] = False
        
        validation_result['checks_performed'].append('必須フィールド確認')
        
        # 2. 請求項の整合性チェック
        claims_validation = self._validate_claims(patent_data.get('claims', []))
        validation_result['warnings'].extend(claims_validation['warnings'])
        validation_result['errors'].extend(claims_validation['errors'])
        validation_result['checks_performed'].append('請求項整合性')
        
        # 3. 実施形態の存在確認
        embodiment_validation = self._validate_embodiments(patent_data.get('detailed_description', ''))
        validation_result['warnings'].extend(embodiment_validation['warnings'])
        validation_result['checks_performed'].append('実施形態確認')
        
        # 4. 法的表現の適切性チェック
        legal_validation = self._validate_legal_expressions(patent_data)
        validation_result['warnings'].extend(legal_validation['warnings'])
        validation_result['recommendations'].extend(legal_validation['recommendations'])
        validation_result['checks_performed'].append('法的表現適切性')
        
        # 5. 化学分野特有の検証（化学処理が有効な場合）
        if self.enable_chemical_processing:
            chemical_validation = self._validate_chemical_content(patent_data)
            validation_result['warnings'].extend(chemical_validation['warnings'])
            validation_result['recommendations'].extend(chemical_validation['recommendations'])
            validation_result['checks_performed'].append('化学内容検証')
        
        # 6. テキスト品質チェック
        text_quality_validation = self._validate_text_quality(patent_data)
        validation_result['warnings'].extend(text_quality_validation['warnings'])
        validation_result['checks_performed'].append('テキスト品質')
        
        # 7. 参照整合性チェック
        reference_validation = self._validate_references(patent_data)
        validation_result['warnings'].extend(reference_validation['warnings'])
        validation_result['checks_performed'].append('参照整合性')
        
        # 総合品質スコアの計算
        validation_result['quality_score'] = self._calculate_overall_quality_score(patent_data, validation_result)
        
        # エラーがある場合は無効とマーク
        if validation_result['errors']:
            validation_result['is_valid'] = False
        
        return validation_result
    
    def _validate_claims(self, claims: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """請求項の整合性チェック"""
        result = {'warnings': [], 'errors': []}
        
        if not claims:
            result['errors'].append("請求項が存在しません")
            return result
        
        # 請求項番号の連続性チェック
        claim_numbers = []
        for claim in claims:
            claim_num = claim.get('claim_number', '')
            if claim_num.isdigit():
                claim_numbers.append(int(claim_num))
        
        if claim_numbers:
            claim_numbers.sort()
            expected_numbers = list(range(1, len(claim_numbers) + 1))
            
            if claim_numbers != expected_numbers:
                result['warnings'].append(f"請求項番号が連続していません: {claim_numbers}")
        
        # 独立請求項の存在チェック
        independent_claims = 0
        dependent_claims = 0
        
        for claim in claims:
            claim_text = claim.get('claim_text', '')
            if '請求項' in claim_text and ('記載の' in claim_text or 'に記載の' in claim_text):
                dependent_claims += 1
            else:
                independent_claims += 1
        
        if independent_claims == 0:
            result['errors'].append("独立請求項が存在しません")
        
        if dependent_claims == 0 and len(claims) > 1:
            result['warnings'].append("従属請求項が存在しません（複数請求項がある場合）")
        
        # 請求項テキストの品質チェック
        for i, claim in enumerate(claims, 1):
            claim_text = claim.get('claim_text', '')
            if len(claim_text) < 50:
                result['warnings'].append(f"請求項{i}のテキストが短すぎます（{len(claim_text)}文字）")
            
            # 特許特有の表現の存在チェック
            if not any(expr in claim_text for expr in ['を備える', 'を有する', 'からなる', 'を含む']):
                result['warnings'].append(f"請求項{i}に構成要素を示す法的表現が不足しています")
        
        return result
    
    def _validate_embodiments(self, detailed_description: str) -> Dict[str, List[str]]:
        """実施形態の存在確認"""
        result = {'warnings': []}
        
        if not detailed_description:
            result['warnings'].append("詳細な説明が存在しません")
            return result
        
        # 実施形態関連キーワードの存在チェック
        embodiment_keywords = ['実施の形態', '実施例', '具体例', '実施形態', '実施態様']
        found_keywords = [kw for kw in embodiment_keywords if kw in detailed_description]
        
        if not found_keywords:
            result['warnings'].append("実施形態を示すキーワードが見つかりません")
        
        # 実施形態の説明の詳細度チェック
        if len(detailed_description) < 500:
            result['warnings'].append(f"詳細な説明が短すぎます（{len(detailed_description)}文字）")
        
        return result
    
    def _validate_legal_expressions(self, patent_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """法的表現の適切性チェック"""
        result = {'warnings': [], 'recommendations': []}
        
        combined_text = patent_data.get('combined_text', '')
        if not combined_text:
            return result
        
        legal_analysis = self.analyze_legal_content(combined_text)
        
        # クリティカルな法的表現の存在チェック
        if not legal_analysis['has_critical_expressions']:
            result['warnings'].append("重要な法的表現（「ことを特徴とする」等）が不足しています")
        
        # 請求項特有の法的表現チェック
        if not legal_analysis['has_claim_expressions']:
            result['warnings'].append("請求項特有の法的表現が不足しています")
        
        # 法的品質スコアに基づく推奨事項
        quality_score = legal_analysis['legal_quality_score']
        if quality_score < 0.3:
            result['recommendations'].append("法的表現の使用頻度を増やすことを推奨します")
        elif quality_score < 0.6:
            result['recommendations'].append("より多様な法的表現の使用を推奨します")
        
        return result
    
    def _validate_chemical_content(self, patent_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """化学分野特有の検証"""
        result = {'warnings': [], 'recommendations': []}
        
        combined_text = patent_data.get('combined_text', '')
        if not combined_text:
            return result
        
        chemical_analysis = patent_data.get('chemical_analysis', {})
        if not chemical_analysis.get('enabled'):
            return result
        
        # 化学的エンティティの存在チェック
        if chemical_analysis['total_entities'] == 0:
            result['warnings'].append("化学式や化学的表現が見つかりません（C分野特許として適切か確認してください）")
        
        # 化学的複雑度チェック
        complexity_score = chemical_analysis.get('complexity_score', 0.0)
        if complexity_score < 0.1:
            result['recommendations'].append("化学的内容の詳細度を向上させることを推奨します")
        
        # カテゴリバランスチェック
        category_counts = chemical_analysis.get('category_counts', {})
        if len(category_counts) == 1:
            result['recommendations'].append("化学的表現の多様性を向上させることを推奨します")
        
        return result
    
    def _validate_text_quality(self, patent_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """テキスト品質チェック"""
        result = {'warnings': []}
        
        # 文章数チェック
        sentence_count = patent_data.get('sentence_count', 0)
        if sentence_count < 50:
            result['warnings'].append(f"文章数が少なすぎます（{sentence_count}文）")
        
        # タイトルの適切性チェック
        title = patent_data.get('title', '')
        if len(title) < 10:
            result['warnings'].append(f"発明の名称が短すぎます（{len(title)}文字）")
        
        # 要約の存在と適切性
        abstract = patent_data.get('abstract', '')
        if not abstract:
            result['warnings'].append("要約が存在しません")
        elif len(abstract) < 100:
            result['warnings'].append(f"要約が短すぎます（{len(abstract)}文字）")
        
        return result
    
    def _validate_references(self, patent_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """参照整合性チェック"""
        result = {'warnings': []}
        
        # 引用文献の存在チェック
        citations = patent_data.get('citations', [])
        if not citations:
            result['warnings'].append("引用文献が存在しません")
        
        # 発明者・出願人の存在チェック
        inventors = patent_data.get('inventors', [])
        applicants = patent_data.get('applicants', [])
        
        if not inventors:
            result['warnings'].append("発明者情報が存在しません")
        
        if not applicants:
            result['warnings'].append("出願人情報が存在しません")
        
        # IPC分類の存在チェック
        ipc_classification = patent_data.get('ipc_classification', [])
        if not ipc_classification:
            result['warnings'].append("IPC分類が存在しません")
        
        return result
    
    def _calculate_overall_quality_score(self, patent_data: Dict[str, Any], validation_result: Dict[str, Any]) -> float:
        """総合品質スコアの計算"""
        base_score = 1.0
        
        # エラーによる減点
        error_count = len(validation_result['errors'])
        base_score -= error_count * 0.2
        
        # 警告による減点
        warning_count = len(validation_result['warnings'])
        base_score -= warning_count * 0.05
        
        # 要素別のボーナス/ペナルティ
        
        # 文章数ボーナス
        sentence_count = patent_data.get('sentence_count', 0)
        if sentence_count > 100:
            base_score += 0.1
        
        # 請求項数ボーナス
        claims_count = patent_data.get('claims_count', 0)
        if claims_count >= 3:
            base_score += 0.1
        
        # 化学的複雑度ボーナス（化学処理が有効な場合）
        if self.enable_chemical_processing:
            chemical_analysis = patent_data.get('chemical_analysis', {})
            if chemical_analysis.get('enabled'):
                complexity_score = chemical_analysis.get('complexity_score', 0.0)
                base_score += complexity_score * 0.2
        
        # 法的表現品質ボーナス
        combined_text = patent_data.get('combined_text', '')
        if combined_text:
            legal_analysis = self.analyze_legal_content(combined_text)
            legal_quality = legal_analysis.get('legal_quality_score', 0.0)
            base_score += legal_quality * 0.15
        
        # 0.0-1.0の範囲に正規化
        final_score = max(0.0, min(1.0, base_score))
        
        return round(final_score, 3)
    
    def parse_xml_file(self, xml_path: str) -> Dict[str, Any]:
        """
        特許XMLファイルを解析してセクション別にデータを抽出
        
        Args:
            xml_path: XMLファイルのパス
            
        Returns:
            セクション別のデータ辞書
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            patent_data = {
                'patent_number': self._get_text(root, './/pat:PublicationNumber'),
                'publication_date': self._get_text(root, './/com:PublicationDate'),
                'filing_date': self._get_text(root, './/pat:FilingDate'),
                'title': self._get_text(root, './/pat:InventionTitle'),
                'abstract': self._extract_abstract(root),
                'technical_field': self._extract_technical_field(root),
                'background_art': self._extract_background_art(root),
                'summary': self._extract_summary(root),
                'detailed_description': self._extract_detailed_description(root),
                'claims': self._extract_claims(root),
                'inventors': self._extract_inventors(root),
                'applicants': self._extract_applicants(root),
                'ipc_classification': self._extract_ipc_classification(root),
                'citations': self._extract_citations(root)
            }
            
            return patent_data
            
        except ET.ParseError as e:
            print(f"XML解析エラー: {e}")
            return {}
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
            return {}
    
    def _get_text(self, root, xpath: str) -> str:
        """XPathでテキストを取得"""
        try:
            element = root.find(xpath, self.namespaces)
            return element.text.strip() if element is not None and element.text else ""
        except:
            return ""
    
    def _clean_xml_text(self, text: str) -> str:
        """XMLから抽出したテキストのクリーニング（段落番号対応版）"""
        if not text:
            return ""
        
        # XMLタグの除去と改行の正規化
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'<com:Br\s*/>', '\n', text)
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_text_with_paragraph_numbers(self, element) -> str:
        """
        段落番号【XXXX】を含めてテキストを抽出
        
        Args:
            element: XMLエレメント
            
        Returns:
            段落番号付きテキスト
        """
        if element is None:
            return ""
        
        text_parts = []
        
        # 直接の子要素を処理
        for child in element:
            if child.tag.endswith('}P'):  # com:P または pat:P
                # 段落番号を取得
                p_number = child.get('{http://www.wipo.int/standards/XMLSchema/ST96/Common}pNumber')
                if not p_number:
                    p_number = child.get('pNumber')  # 名前空間なしも試行
                
                # 段落のテキストを取得
                p_text = ET.tostring(child, encoding='unicode', method='text')
                p_text = self._clean_xml_text(p_text)
                
                if p_text:
                    if p_number:
                        # 段落番号付きで追加
                        text_parts.append(f"【{p_number}】\n{p_text}")
                    else:
                        # 段落番号なしで追加
                        text_parts.append(p_text)
            else:
                # P以外のタグは再帰処理
                child_text = self._extract_text_with_paragraph_numbers(child)
                if child_text:
                    text_parts.append(child_text)
        
        # 直接テキストがある場合も含める
        if element.text and element.text.strip():
            text_parts.insert(0, element.text.strip())
        
        return '\n\n'.join(text_parts)
    
    def _extract_abstract(self, root) -> str:
        """要約の抽出"""
        abstract_elem = root.find('.//pat:Abstract', self.namespaces)
        if abstract_elem is not None:
            text = ET.tostring(abstract_elem, encoding='unicode', method='text')
            return self._clean_xml_text(text)
        return ""
    
    def _extract_technical_field(self, root) -> str:
        """技術分野の抽出"""
        field_elem = root.find('.//pat:TechnicalField', self.namespaces)
        if field_elem is not None:
            text = ET.tostring(field_elem, encoding='unicode', method='text')
            return self._clean_xml_text(text)
        return ""
    
    def _extract_background_art(self, root) -> str:
        """背景技術の抽出"""
        bg_elem = root.find('.//pat:BackgroundArt', self.namespaces)
        if bg_elem is not None:
            text = ET.tostring(bg_elem, encoding='unicode', method='text')
            return self._clean_xml_text(text)
        return ""
    
    def _extract_summary(self, root) -> str:
        """発明の概要の抽出"""
        summary_elem = root.find('.//pat:Summary', self.namespaces)
        if summary_elem is not None:
            text = ET.tostring(summary_elem, encoding='unicode', method='text')
            return self._clean_xml_text(text)
        return ""
    
    def _extract_detailed_description(self, root) -> str:
        """
        詳細な説明の抽出（発明を実施するための形態）
        注意: EmbodimentDescription優先、見つからない場合DetailedDescription、BestMode、InventionModeを使用
        段階1: BestModeを追加（2025-08-01）
        段階2: InventionModeも追加（2025-08-01）
        段階3: 文字数制限とセクション選択機能追加（2025-08-01）
        段階4: 段落番号【XXXX】を保持（2025-08-01）
        """
        # タグマッピング
        tag_mapping = {
            'EmbodimentDescription': './/pat:EmbodimentDescription',
            'DetailedDescription': './/pat:DetailedDescription',
            'BestMode': './/pat:BestMode',
            'InventionMode': './/jppat:InventionMode'
        }
        
        # 設定されたソースのみを使用
        for source in self.description_sources:
            if source not in tag_mapping:
                continue
                
            xpath = tag_mapping[source]
            elem = root.find(xpath, self.namespaces)
            
            if elem is not None:
                # 段落番号を含めてテキストを抽出
                cleaned_text = self._extract_text_with_paragraph_numbers(elem)
                
                if cleaned_text:
                    # 文字数制限の適用
                    if len(cleaned_text) > self.max_description_length:
                        logger.warning(f"{source}の文字数が制限を超えています: {len(cleaned_text)} > {self.max_description_length}")
                        # 制限内に収める（末尾に省略記号を追加）
                        cleaned_text = cleaned_text[:self.max_description_length - 3] + "..."
                    
                    logger.info(f"{source}から実施形態を抽出しました（段落番号付き、最終文字数: {len(cleaned_text)}文字）")
                    return cleaned_text
        
        return ""
    
    def _extract_claims(self, root) -> List[Dict[str, str]]:
        """特許請求の範囲の抽出"""
        claims = []
        claims_elem = root.find('.//pat:Claims', self.namespaces)
        if claims_elem is not None:
            for claim in claims_elem.findall('.//pat:Claim', self.namespaces):
                claim_num = self._get_text(claim, './/pat:ClaimNumber')
                claim_text_elem = claim.find('.//pat:ClaimText', self.namespaces)
                if claim_text_elem is not None:
                    claim_text = ET.tostring(claim_text_elem, encoding='unicode', method='text')
                    claims.append({
                        'claim_number': claim_num,
                        'claim_text': self._clean_xml_text(claim_text)
                    })
        return claims
    
    def _extract_inventors(self, root) -> List[str]:
        """発明者の抽出"""
        inventors = []
        inventor_elems = root.findall('.//jppat:Inventor//com:EntityName', self.namespaces)
        for elem in inventor_elems:
            if elem.text:
                inventors.append(elem.text.strip())
        return inventors
    
    def _extract_applicants(self, root) -> List[str]:
        """出願人の抽出"""
        applicants = []
        applicant_elems = root.findall('.//jppat:Applicant//com:EntityName', self.namespaces)
        for elem in applicant_elems:
            if elem.text:
                applicants.append(elem.text.strip())
        return applicants
    
    def _extract_ipc_classification(self, root) -> List[str]:
        """IPC分類の抽出"""
        classifications = []
        ipc_elems = root.findall('.//pat:MainClassification', self.namespaces)
        for elem in ipc_elems:
            if elem.text:
                classifications.append(elem.text.strip())
        return classifications
    
    def _extract_citations(self, root) -> List[str]:
        """引用文献の抽出"""
        citations = []
        citation_elems = root.findall('.//com:PatentCitationText', self.namespaces)
        for elem in citation_elems:
            if elem.text:
                citations.append(elem.text.strip())
        return citations
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """
        文分割
        
        Args:
            text: 入力テキスト
            
        Returns:
            文のリスト
        """
        if not text:
            return []
            
        if self.language == "japanese":
            sentences = re.split(r'[。！？]', text)
            sentences = [s.strip() for s in sentences if s.strip()]
        else:
            sentences = sent_tokenize(text)
            
        return sentences
    
    def process_xml_files(self, xml_dir: str) -> pd.DataFrame:
        """
        XMLファイルの一括処理
        
        Args:
            xml_dir: XMLファイルが格納されているディレクトリ
            
        Returns:
            処理済みDataFrame
        """
        xml_files = list(Path(xml_dir).glob("**/*.xml"))
        processed_data = []
        
        for xml_file in xml_files:
            try:
                patent_data = self.parse_xml_file(str(xml_file))
                if patent_data:
                    patent_data['xml_file_path'] = str(xml_file)
                    patent_data['file_name'] = xml_file.name
                    
                    combined_text = self._combine_text_sections(patent_data)
                    patent_data['combined_text'] = self.enhanced_clean_text(combined_text)
                    
                    # 化学的内容の分析
                    if self.enable_chemical_processing:
                        chemical_analysis = self.analyze_chemical_content(patent_data['combined_text'])
                        patent_data['chemical_analysis'] = chemical_analysis
                    
                    # 法的表現の分析
                    legal_analysis = self.analyze_legal_content(patent_data['combined_text'])
                    patent_data['legal_analysis'] = legal_analysis
                    
                    # データ品質チェック
                    validation_result = self.validate_patent_data(patent_data)
                    patent_data['validation'] = validation_result
                    
                    patent_data['sentences'] = self.tokenize_sentences(patent_data['combined_text'])
                    patent_data['sentence_count'] = len(patent_data['sentences'])
                    
                    # Claims情報をテキスト形式で格納
                    claims_text = []
                    if patent_data.get('claims'):
                        for claim in patent_data['claims']:
                            claims_text.append(claim.get('claim_text', ''))
                    patent_data['claims_text'] = ' '.join(claims_text)
                    patent_data['claims_count'] = len(patent_data.get('claims', []))
                    
                    processed_data.append(patent_data)
                    
            except Exception as e:
                print(f"ファイル処理エラー {xml_file}: {e}")
                continue
        
        return pd.DataFrame(processed_data)
    
    def _combine_text_sections(self, patent_data: Dict[str, Any]) -> str:
        """
        特許データの各セクションを結合
        
        Args:
            patent_data: 特許データ辞書
            
        Returns:
            結合されたテキスト
        """
        text_sections = []
        
        sections_order = ['title', 'abstract', 'technical_field', 'background_art', 
                         'summary', 'detailed_description']
        
        for section in sections_order:
            content = patent_data.get(section, '')
            if content:
                text_sections.append(content)
        
        # Claims情報も追加
        if patent_data.get('claims'):
            for claim in patent_data['claims']:
                claim_text = claim.get('claim_text', '')
                if claim_text:
                    text_sections.append(claim_text)
        
        return '\n\n'.join(text_sections)
    
    def create_chatml_dataset(self, data: pd.DataFrame, output_path: str) -> None:
        """
        ChatML形式の学習データを作成（請求項→実施形態）
        
        Args:
            data: 処理済みDataFrame
            output_path: 出力先パス
        """
        output_file_path = Path(output_path)
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        chatml_data = []
        
        for _, row in data.iterrows():
            patent_id = row.get('patent_number', '')
            claims = row.get('claims', [])
            detailed_description = row.get('detailed_description', '')
            
            # 実施形態と請求項が両方存在する場合のみ学習データを作成
            if detailed_description.strip() and claims:
                # 全請求項をまとめた学習データを作成（1公報=1サンプル）
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
                            "created_at": datetime.now().isoformat()
                        }
                    }
                    
                    chatml_data.append(chatml_record)
        
        # JSON出力（型変換適用）
        chatml_data_serializable = self._convert_to_json_serializable(chatml_data)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chatml_data_serializable, f, ensure_ascii=False, indent=2)
        
        print(f"ChatML学習データを出力しました: {output_path}")
        print(f"作成された学習サンプル数: {len(chatml_data)}")
    
    def _convert_to_json_serializable(self, obj: Any) -> Any:
        """
        JSON出力用にデータ型を変換
        注意: pandas/numpyの型はJSONシリアライズできないため変換が必要
        
        Args:
            obj: 変換対象のオブジェクト
            
        Returns:
            JSON出力可能な型に変換されたオブジェクト
        """
        if hasattr(obj, 'dtype') and 'int' in str(obj.dtype):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_to_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        else:
            return obj
    
    def export_to_json(self, data: pd.DataFrame, output_path: str, 
                      include_metadata: bool = True, 
                      compact_format: bool = False) -> None:
        """
        処理済みデータをJSON形式で出力（学習データ用）
        
        Args:
            data: 出力するDataFrame
            output_path: JSON出力先パス
            include_metadata: メタデータ（出願人、発明者等）を含むかどうか
            compact_format: コンパクト形式（テキストのみ）で出力するかどうか
        """
        output_file_path = Path(output_path)
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = []
        
        for _, row in data.iterrows():
            patent_record = {
                'patent_id': row.get('patent_number', ''),
                'title': row.get('title', ''),
                'abstract': row.get('abstract', ''),
                'technical_field': row.get('technical_field', ''),
                'background_art': row.get('background_art', ''),
                'detailed_description': row.get('detailed_description', ''),
                'combined_text': row.get('combined_text', ''),
                'sentences': row.get('sentences', []),
                'sentence_count': int(row.get('sentence_count', 0)),  # 明示的にint型変換
                'claims': row.get('claims', []),
                'claims_text': row.get('claims_text', ''),
                'claims_count': int(row.get('claims_count', 0)),  # 明示的にint型変換
            }
            
            if include_metadata:
                patent_record.update({
                    'publication_date': row.get('publication_date', ''),
                    'filing_date': row.get('filing_date', ''),
                    'inventors': row.get('inventors', []),
                    'applicants': row.get('applicants', []),
                    'ipc_classification': row.get('ipc_classification', []),
                    'citations': row.get('citations', []),
                    'xml_file_path': row.get('xml_file_path', ''),
                })
            
            if compact_format:
                patent_record = {
                    'patent_id': patent_record['patent_id'],
                    'title': patent_record['title'],
                    'text': patent_record['combined_text'],
                    'claims': [claim.get('claim_text', '') for claim in row.get('claims', [])],
                }
            
            export_data.append(patent_record)
        
        # JSON出力（型変換適用）
        export_data_serializable = self._convert_to_json_serializable(export_data)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data_serializable, f, ensure_ascii=False, indent=2)
            
        print(f"データをJSONファイルに出力しました: {output_path}")
        print(f"出力レコード数: {len(export_data)}")
        
    def create_training_dataset(self, data: pd.DataFrame, output_dir: str) -> None:
        """
        機械学習用の複数形式でデータセットを作成
        
        Args:
            data: 元データのDataFrame
            output_dir: 出力ディレクトリ
        """
        output_directory = Path(output_dir)
        output_directory.mkdir(parents=True, exist_ok=True)
        
        # 1. 完全版（全データ含む）
        self.export_to_json(
            data, 
            str(output_directory / "complete_dataset.json"),
            include_metadata=True, 
            compact_format=False
        )
        
        # 2. 学習用コンパクト版（テキストのみ）
        self.export_to_json(
            data, 
            str(output_directory / "training_dataset.json"),
            include_metadata=False, 
            compact_format=True
        )
        
        # 3. セクション別データ
        sections_data = []
        for _, row in data.iterrows():
            patent_id = row.get('patent_number', '')
            
            # patent_idが空の場合、ダミーIDを生成
            if not patent_id or patent_id.strip() == '':
                # ファイル名やインデックスからダミーIDを生成
                file_name = row.get('file_name', 'unknown')
                dummy_id = f"patent_{hash(file_name) % 100000:05d}"  # 5桁のダミーID
                patent_id = dummy_id
                logger.warning(f"空のpatent_idを検出、ダミーIDを生成: {patent_id}")
            
            sections = [
                {'patent_id': patent_id, 'section': 'title', 'text': row.get('title', '')},
                {'patent_id': patent_id, 'section': 'abstract', 'text': row.get('abstract', '')},
                {'patent_id': patent_id, 'section': 'technical_field', 'text': row.get('technical_field', '')},
                {'patent_id': patent_id, 'section': 'background_art', 'text': row.get('background_art', '')},
                {'patent_id': patent_id, 'section': 'detailed_description', 'text': row.get('detailed_description', '')},
            ]
            
            # 請求項を個別に追加（詳細分析用）
            claims = row.get('claims', [])
            for claim in claims:
                sections.append({
                    'patent_id': patent_id,
                    'section': f"claim_{claim.get('claim_number', '')}",
                    'text': claim.get('claim_text', '')
                })
            
            # 請求項を統合してchat format用の統合セクションも追加
            if claims:
                combined_claims_text = []
                for claim in claims:
                    claim_text = claim.get('claim_text', '')
                    claim_number = claim.get('claim_number', '')
                    if claim_text:
                        # 【請求項N】形式で統合
                        formatted_claim = f"【請求項{claim_number}】{claim_text}" if claim_number else claim_text
                        combined_claims_text.append(formatted_claim)
                
                if combined_claims_text:
                    sections.append({
                        'patent_id': patent_id,
                        'section': 'claims',  # chat format用の統合セクション
                        'text': '\n'.join(combined_claims_text)
                    })
            
            sections_data.extend(sections)
        
        # セクション別データをJSON出力（型変換適用）
        sections_data_serializable = self._convert_to_json_serializable(sections_data)
        with open(str(output_directory / "sections_dataset.json"), 'w', encoding='utf-8') as f:
            json.dump(sections_data_serializable, f, ensure_ascii=False, indent=2)
            
        # 4. 統計情報とメタデータ
        stats = {
            'dataset_info': {
                'created_at': datetime.now().isoformat(),
                'total_patents': int(len(data)),  # 明示的にint型変換
                'total_sentences': int(data['sentence_count'].sum() if 'sentence_count' in data.columns else 0),
                'total_claims': int(data['claims_count'].sum() if 'claims_count' in data.columns else 0),
            },
            'file_descriptions': {
                'complete_dataset.json': '全データを含む完全版（メタデータ付き）',
                'training_dataset.json': '学習用コンパクト版（テキストのみ）',
                'sections_dataset.json': 'セクション別に分割されたデータ',
                'dataset_stats.json': 'このファイル - データセット統計情報'
            }
        }
        
        # 5. ChatML形式の学習データ
        self.create_chatml_dataset(data, str(output_directory / "chatml_training.json"))
        
        # 統計情報を更新（ChatMLファイル情報を追加）
        stats['file_descriptions']['chatml_training.json'] = 'ChatML形式の学習データ（請求項→実施形態）'
        
        # 統計情報をJSON出力
        with open(str(output_directory / "dataset_stats.json"), 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
            
        print(f"\n=== 学習データセット作成完了 ===")
        print(f"出力ディレクトリ: {output_directory}")
        print(f"作成ファイル:")
        for file_name, description in stats['file_descriptions'].items():
            file_path = output_directory / file_name
            file_size = file_path.stat().st_size if file_path.exists() else 0
            print(f"  - {file_name}: {description} ({file_size:,} bytes)")


# 定数定義
DEFAULT_MODE = "single"
SUPPORTED_MODES = ['single', 'bulk', 'quick']
LINE_SEPARATOR = "=" * 50
MAX_TEXT_PREVIEW_LENGTH = 200
MAX_CLAIMS_TO_DISPLAY = 2
MAX_CLAIM_TEXT_LENGTH = 150
MAX_COMBINED_TEXT_LENGTH = 300


def _setup_data_discovery():
    """データディスカバリーモジュールのセットアップ"""
    try:
        from ..utils.data_discovery import get_auto_data_path, DataDiscovery
        return get_auto_data_path, DataDiscovery
    except ImportError:
        print("警告: data_discovery モジュールが見つかりません。"
              "従来の方法を使用します。")
        return None, None


def _find_raw_data_dir(project_root: Path) -> Optional[Path]:
    """data/raw配下のXMLファイルを含むディレクトリを検索"""
    data_raw_dir = project_root / "data" / "raw"
    if not data_raw_dir.exists():
        return None
        
    for item in data_raw_dir.iterdir():
        if not item.is_dir():
            continue
            
        xml_files = list(item.glob("*.xml"))
        if xml_files:
            print(f"📁 data/raw/{item.name} を発見 ({len(xml_files)}個のXML)")
            return item
    
    return None


def _find_jpb_data_dir(project_root: Path) -> Optional[Path]:
    """JPB発行分のDOCUMENTディレクトリから適切なXMLディレクトリを検索"""
    import re
    
    data_dir = project_root / "data"
    if not data_dir.exists():
        return None
        
    jpb_pattern = re.compile(r'JPB_\d+_\d+発行分')
    
    for item in data_dir.iterdir():
        if not (item.is_dir() and jpb_pattern.match(item.name)):
            continue
            
        document_dir = item / "DOCUMENT"
        if not document_dir.exists():
            continue
            
        xml_files = list(document_dir.glob("**/*.xml"))
        if not xml_files:
            continue
            
        print(f"📁 {item.name}/DOCUMENT を発見 ({len(xml_files)}個のXML)")
        
        # 単一XMLファイルを含む適切なディレクトリを探す
        suitable_dir = _find_suitable_xml_dir(xml_files)
        if suitable_dir:
            return suitable_dir
    
    return None


def _find_suitable_xml_dir(xml_files: List[Path]) -> Optional[Path]:
    """XMLファイルリストから適切なディレクトリを選択"""
    for xml_file in xml_files[:5]:  # 最初の5つをチェック
        parent_dir = xml_file.parent
        
        # DOCUMENTディレクトリ直下は避ける
        if parent_dir.name == "DOCUMENT":
            continue
            
        # 小さいディレクトリを優先（3個以下のXMLファイル）
        xml_count = len(list(parent_dir.glob("*.xml")))
        if xml_count <= 3:
            return parent_dir
    
    return None


def _get_fallback_data_dir() -> Optional[Path]:
    """フォールバック用のデータディレクトリを動的に検索"""
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]
    
    # data/raw配下を優先検索
    raw_dir = _find_raw_data_dir(project_root)
    if raw_dir:
        return raw_dir
    
    # JPB発行分を検索
    jpb_dir = _find_jpb_data_dir(project_root)
    if jpb_dir:
        return jpb_dir
    
    print("⚠️  利用可能なデータディレクトリが見つかりませんでした")
    return None


def _resolve_data_path(sample_data_path: Optional[str], mode: str) -> Path:
    """データパスを解決する"""
    if sample_data_path is not None:
        sample_dir = Path(sample_data_path)
        print(f"📋 指定されたパス: {sample_dir}")
        return sample_dir
    
    get_auto_data_path, DataDiscovery = _setup_data_discovery()
    
    # 動的データ検出を試行
    sample_dir = None
    if get_auto_data_path is not None:
        auto_path = get_auto_data_path(mode)
        if auto_path:
            sample_dir = Path(auto_path)
            print(f"🔍 自動検出されたパス ({mode}モード): {sample_dir}")
            
            # ディスカバリーレポートを表示
            if DataDiscovery is not None:
                discovery = DataDiscovery()
                print("\n" + LINE_SEPARATOR)
                discovery.print_discovery_report()
                print(LINE_SEPARATOR + "\n")
    
    # 自動検出が失敗した場合のフォールバック処理
    if sample_dir is None:
        print("⚠️  自動検出に失敗。フォールバック検索を実行中...")
        sample_dir = _get_fallback_data_dir()
        
        if sample_dir is None:
            error_msg = ("❌ エラー: 利用可能なXMLデータが見つかりません\n"
                        "   以下を確認してください：\n"
                        "   - data/raw/ 配下にXMLファイルを含む"
                        "ディレクトリが存在するか\n"
                        "   - JPB発行分のDOCUMENTディレクトリに"
                        "XMLファイルが存在するか")
            print(error_msg)
            raise FileNotFoundError("XMLデータディレクトリが見つかりません")
        else:
            print(f"✅ フォールバック検索成功: {sample_dir}")
    
    return sample_dir


def _find_xml_file(sample_dir: Path) -> Path:
    """指定ディレクトリからXMLファイルを検索"""
    xml_files = list(sample_dir.glob("*.xml"))
    if not xml_files:
        raise FileNotFoundError(
            f"エラー: {sample_dir} 内にXMLファイルが見つかりません"
        )
    return xml_files[0]


def _display_patent_info(patent_data: Dict[str, Any]) -> None:
    """特許データの基本情報を表示"""
    if not patent_data:
        return
    
    print(f"特許番号: {patent_data.get('patent_number')}")
    print(f"発明の名称: {patent_data.get('title')}")
    print(f"公開日: {patent_data.get('publication_date')}")
    print(f"出願日: {patent_data.get('filing_date')}")
    print(f"発明者: {', '.join(patent_data.get('inventors', []))}")
    print(f"出願人: {', '.join(patent_data.get('applicants', []))}")
    print(f"IPC分類: {', '.join(patent_data.get('ipc_classification', []))}")


def _display_patent_content(patent_data: Dict[str, Any]) -> None:
    """特許データの内容を表示"""
    # 要約表示
    abstract = patent_data.get('abstract', '')
    print(f"\n要約:")
    if len(abstract) > MAX_TEXT_PREVIEW_LENGTH:
        print(abstract[:MAX_TEXT_PREVIEW_LENGTH] + "...")
    else:
        print(abstract)
    
    # 技術分野表示
    technical_field = patent_data.get('technical_field', '')
    print(f"\n技術分野:")
    if len(technical_field) > MAX_TEXT_PREVIEW_LENGTH:
        print(technical_field[:MAX_TEXT_PREVIEW_LENGTH] + "...")
    else:
        print(technical_field)
    
    # 請求項表示
    print(f"\n特許請求の範囲:")
    claims = patent_data.get('claims', [])
    for i, claim in enumerate(claims[:MAX_CLAIMS_TO_DISPLAY], 1):
        claim_text = claim.get('claim_text', '')
        claim_number = claim.get('claim_number')
        if len(claim_text) > MAX_CLAIM_TEXT_LENGTH:
            display_text = claim_text[:MAX_CLAIM_TEXT_LENGTH] + "..."
        else:
            display_text = claim_text
        print(f"請求項{claim_number}: {display_text}")
    
    # 引用文献数
    citations_count = len(patent_data.get('citations', []))
    print(f"\n引用文献数: {citations_count}")


def _display_dataframe_info(df: pd.DataFrame) -> None:
    """DataFrameの情報を表示"""
    if len(df) == 0:
        return
    
    print(f"データフレームのカラム: {list(df.columns)}")
    
    sentence_count = (df['sentence_count'].iloc[0] 
                     if 'sentence_count' in df.columns else 'N/A')
    print(f"文章数: {sentence_count}")
    
    claims_count = (df['claims_count'].iloc[0] 
                   if 'claims_count' in df.columns else 'N/A')
    print(f"請求項数: {claims_count}")
    
    combined_text = (df['combined_text'].iloc[0] 
                    if 'combined_text' in df.columns else "")
    print(f"\n結合テキスト（最初の{MAX_COMBINED_TEXT_LENGTH}文字）:")
    if len(combined_text) > MAX_COMBINED_TEXT_LENGTH:
        print(combined_text[:MAX_COMBINED_TEXT_LENGTH] + "...")
    else:
        print(combined_text)


def _get_output_directory(sample_data_path: Optional[str]) -> Path:
    """出力ディレクトリを取得"""
    if sample_data_path is None:
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]
        return project_root / "data" / "processed"
    else:
        return Path(sample_data_path).parent / "processed"


def _parse_command_line_args() -> Tuple[Optional[str], str]:
    """コマンドライン引数を解析"""
    import sys
    
    sample_path = None
    mode = DEFAULT_MODE
    
    if len(sys.argv) > 1:
        if sys.argv[1] in SUPPORTED_MODES:
            # 第1引数がモード指定の場合
            mode = sys.argv[1]
            sample_path = sys.argv[2] if len(sys.argv) > 2 else None
        else:
            # 第1引数がパス指定の場合
            sample_path = sys.argv[1]
            if (len(sys.argv) > 2 and sys.argv[2] in SUPPORTED_MODES):
                mode = sys.argv[2]
    
    return sample_path, mode


def main(sample_data_path: Optional[str] = None, mode: str = "single"):
    """
    サンプル実行（動的データ検出対応）
    
    Args:
        sample_data_path: サンプルデータのディレクトリパス
                         （指定しない場合は自動検出）
        mode: 実行モード ('single', 'bulk', 'quick')
    """
    processor = PatentTextProcessor(language="japanese")
    
    try:
        # データパス解決
        sample_dir = _resolve_data_path(sample_data_path, mode)
        
        # モード別処理
        if mode == "bulk":
            # bulkモードの場合は直接一括処理
            print(f"=== ディレクトリ一括処理（bulkモード）: {sample_dir.name} ===")
            df = processor.process_xml_files(str(sample_dir))
            print(f"処理されたファイル数: {len(df)}")
            
            _display_dataframe_info(df)
            
            # JSON出力機能のテスト
            output_dir = _get_output_directory(sample_data_path)
            print(f"\n=== JSON学習データ出力テスト ===")
            processor.create_training_dataset(df, str(output_dir))
            
        else:
            # single, quickモードの場合は単一ファイルテストを実行
            # XMLファイル検索
            xml_file = _find_xml_file(sample_dir)
            
            # 特許XMLファイル解析テスト
            print(f"=== 特許XMLファイル解析テスト: {xml_file.name} ===")
            patent_data = processor.parse_xml_file(str(xml_file))
            
            _display_patent_info(patent_data)
            _display_patent_content(patent_data)
            
            # ディレクトリ一括処理テスト
            print(f"\n=== ディレクトリ一括処理テスト: {sample_dir.name} ===")
            df = processor.process_xml_files(str(sample_dir))
            print(f"処理されたファイル数: {len(df)}")
            
            _display_dataframe_info(df)
            
            # JSON出力機能のテスト
            output_dir = _get_output_directory(sample_data_path)
            print(f"\n=== JSON学習データ出力テスト ===")
            processor.create_training_dataset(df, str(output_dir))
        
    except (FileNotFoundError, Exception) as e:
        print(f"エラーが発生しました: {e}")
        return


if __name__ == "__main__":
    # コマンドライン引数解析
    sample_path, mode = _parse_command_line_args()
    
    print(f"🚀 特許XMLファイル処理を開始")
    print(f"   モード: {mode}")
    if sample_path:
        print(f"   指定パス: {sample_path}")
    else:
        print(f"   パス: 自動検出")
    
    main(sample_path, mode)