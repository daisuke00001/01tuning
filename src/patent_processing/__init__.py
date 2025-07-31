"""
特許データ処理モジュール

ST96 XMLフォーマット対応の特許文書解析と前処理機能を提供
"""

from .text_processor import PatentTextProcessor

__all__ = ['PatentTextProcessor']