"""
データディスカバリーユーティリティ
プロジェクト内のXMLファイルを動的に検出・取得
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json


class DataDiscovery:
    """データディスカバリークラス"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初期化
        
        Args:
            project_root: プロジェクトルートパス（指定しない場合は自動検出）
        """
        if project_root is None:
            self.project_root = self._find_project_root()
        else:
            self.project_root = Path(project_root)
        
        self.data_dir = self.project_root / "data"
        
    def _find_project_root(self) -> Path:
        """プロジェクトルートを自動検出"""
        current_file = Path(__file__).resolve()
        # src/utils/data_discovery.py から2つ上の階層がプロジェクトルート
        return current_file.parents[2]
    
    def discover_xml_directories(self) -> Dict[str, List[Path]]:
        """
        XMLファイルを含むディレクトリを発見
        
        Returns:
            ディレクトリタイプ別のパス辞書
        """
        xml_dirs = {
            'raw_data': [],           # data/raw配下
            'jpb_release': [],        # JPB発行分配下
            'single_files': [],       # 単一XMLファイル用ディレクトリ
            'bulk_processing': []     # 一括処理用ディレクトリ
        }
        
        if not self.data_dir.exists():
            print(f"警告: データディレクトリが見つかりません: {self.data_dir}")
            return xml_dirs
        
        # data/raw配下の検索
        raw_dir = self.data_dir / "raw"
        if raw_dir.exists():
            for item in raw_dir.iterdir():
                if item.is_dir():
                    xml_files = list(item.glob("*.xml"))
                    if xml_files:
                        xml_dirs['raw_data'].append(item)
                        xml_dirs['single_files'].append(item)
        
        # JPB発行分の検索
        jpb_pattern = re.compile(r'JPB_\d+_\d+発行分')
        for item in self.data_dir.iterdir():
            if item.is_dir() and jpb_pattern.match(item.name):
                document_dir = item / "DOCUMENT"
                if document_dir.exists():
                    xml_dirs['jpb_release'].append(item)
                    xml_dirs['bulk_processing'].append(document_dir)
                    
                    # JPB配下の単一XMLディレクトリも検索
                    xml_dirs['single_files'].extend(self._find_single_xml_dirs(document_dir))
        
        return xml_dirs
    
    def _find_single_xml_dirs(self, base_dir: Path, max_depth: int = 5) -> List[Path]:
        """
        単一XMLファイルを含むディレクトリを再帰的に検索
        
        Args:
            base_dir: 検索ベースディレクトリ
            max_depth: 最大検索深度
            
        Returns:
            単一XMLファイルを含むディレクトリのリスト
        """
        single_xml_dirs = []
        
        def _recursive_search(current_dir: Path, current_depth: int):
            if current_depth > max_depth:
                return
                
            try:
                xml_files = list(current_dir.glob("*.xml"))
                if len(xml_files) == 1:  # 単一XMLファイル
                    single_xml_dirs.append(current_dir)
                
                # 子ディレクトリを再帰検索
                for child_dir in current_dir.iterdir():
                    if child_dir.is_dir():
                        _recursive_search(child_dir, current_depth + 1)
            except PermissionError:
                pass  # アクセス権限がない場合はスキップ
        
        _recursive_search(base_dir, 0)
        return single_xml_dirs
    
    def get_recommended_paths(self) -> Dict[str, Dict[str, str]]:
        """
        推奨実行パスを取得
        
        Returns:
            推奨パス辞書
        """
        xml_dirs = self.discover_xml_directories()
        recommendations = {
            'single_file_test': {},
            'bulk_processing': {},
            'quick_test': {}
        }
        
        # 単一ファイルテスト推奨パス
        if xml_dirs['single_files']:
            # 最も小さいXMLファイルを持つディレクトリを推奨
            best_single = self._find_smallest_xml_dir(xml_dirs['single_files'])
            if best_single:
                recommendations['single_file_test'] = {
                    'path': str(best_single),
                    'description': f"単一XMLファイルテスト用 ({best_single.name})",
                    'xml_count': len(list(best_single.glob("*.xml")))
                }
        
        # 一括処理推奨パス
        if xml_dirs['bulk_processing']:
            bulk_dir = xml_dirs['bulk_processing'][0]  # 最初のJPB DOCUMENTディレクトリ
            xml_count = len(list(bulk_dir.glob("**/*.xml")))
            recommendations['bulk_processing'] = {
                'path': str(bulk_dir),
                'description': f"一括処理用 (約{xml_count}個のXMLファイル)",
                'xml_count': xml_count
            }
        
        # クイックテスト（data/raw優先）
        if xml_dirs['raw_data']:
            quick_dir = xml_dirs['raw_data'][0]
            recommendations['quick_test'] = {
                'path': str(quick_dir),
                'description': f"クイックテスト用 (data/raw/{quick_dir.name})",
                'xml_count': len(list(quick_dir.glob("*.xml")))
            }
        
        return recommendations
    
    def _find_smallest_xml_dir(self, directories: List[Path]) -> Optional[Path]:
        """最も小さいXMLファイルを持つディレクトリを選択"""
        if not directories:
            return None
        
        min_size = float('inf')
        best_dir = None
        
        for directory in directories:
            xml_files = list(directory.glob("*.xml"))
            if xml_files:
                total_size = sum(xml_file.stat().st_size for xml_file in xml_files)
                if total_size < min_size:
                    min_size = total_size
                    best_dir = directory
        
        return best_dir
    
    def get_auto_path(self, mode: str = "single") -> Optional[str]:
        """
        自動パス取得（text_processor.py での利用想定）
        
        Args:
            mode: 'single' (単一ファイル), 'bulk' (一括処理), 'quick' (クイック)
            
        Returns:
            推奨パス文字列
        """
        recommendations = self.get_recommended_paths()
        
        mode_mapping = {
            'single': 'single_file_test',
            'bulk': 'bulk_processing', 
            'quick': 'quick_test'
        }
        
        target_mode = mode_mapping.get(mode, 'single_file_test')
        
        if target_mode in recommendations and recommendations[target_mode]:
            return recommendations[target_mode]['path']
        
        return None
    
    def print_discovery_report(self) -> None:
        """ディスカバリー結果レポートを出力"""
        print("=== データディスカバリーレポート ===")
        print(f"プロジェクトルート: {self.project_root}")
        print(f"データディレクトリ: {self.data_dir}")
        
        xml_dirs = self.discover_xml_directories()
        
        print(f"\n【発見されたXMLデータ】")
        for category, paths in xml_dirs.items():
            if paths:
                print(f"  {category}: {len(paths)}個のディレクトリ")
                for path in paths[:3]:  # 最初の3つのみ表示
                    xml_count = len(list(path.glob("**/*.xml")))
                    print(f"    - {path.name} ({xml_count}個のXML)")
                if len(paths) > 3:
                    print(f"    ... 他{len(paths)-3}個")
        
        print(f"\n【推奨実行パス】")
        recommendations = self.get_recommended_paths()
        for mode, info in recommendations.items():
            if info:
                print(f"  {mode}: {info['description']}")
                print(f"    パス: {info['path']}")
                print(f"    XMLファイル数: {info['xml_count']}")
            else:
                print(f"  {mode}: 該当なし")
    
    def save_discovery_cache(self, cache_path: Optional[str] = None) -> None:
        """ディスカバリー結果をキャッシュファイルに保存"""
        if cache_path is None:
            cache_file_path = self.project_root / "data" / "discovery_cache.json"
        else:
            cache_file_path = Path(cache_path)
        
        cache_data = {
            'project_root': str(self.project_root),
            'discovery_timestamp': __import__('datetime').datetime.now().isoformat(),
            'xml_directories': {},
            'recommendations': self.get_recommended_paths()
        }
        
        xml_dirs = self.discover_xml_directories()
        for category, paths in xml_dirs.items():
            cache_data['xml_directories'][category] = [str(p) for p in paths]
        
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        print(f"ディスカバリーキャッシュを保存: {cache_file_path}")


def get_auto_data_path(mode: str = "single") -> Optional[str]:
    """
    text_processor.py から簡単に呼び出せる関数
    
    Args:
        mode: 'single', 'bulk', 'quick'
        
    Returns:
        自動検出されたデータパス
    """
    discovery = DataDiscovery()
    return discovery.get_auto_path(mode)


def main():
    """スタンドアローン実行用のメイン関数"""
    discovery = DataDiscovery()
    discovery.print_discovery_report()
    discovery.save_discovery_cache()
    
    print(f"\n=== 自動パス取得テスト ===")
    for mode in ['single', 'bulk', 'quick']:
        auto_path = get_auto_data_path(mode)
        print(f"{mode}モード: {auto_path}")


if __name__ == "__main__":
    main()