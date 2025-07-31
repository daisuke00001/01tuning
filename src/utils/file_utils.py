"""
ファイル操作に関するユーティリティ関数
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Union, List, Dict, Any
import yaml


def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    ディレクトリが存在しない場合は作成
    
    Args:
        directory: ディレクトリパス
        
    Returns:
        Pathオブジェクト
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    設定ファイルの読み込み（YAML/JSON対応）
    
    Args:
        config_path: 設定ファイルのパス
        
    Returns:
        設定内容の辞書
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        if config_path.suffix.lower() in ['.yml', '.yaml']:
            return yaml.safe_load(f)
        elif config_path.suffix.lower() == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """
    設定ファイルの保存
    
    Args:
        config: 設定内容の辞書
        config_path: 保存先パス
    """
    config_path = Path(config_path)
    ensure_dir(config_path.parent)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        if config_path.suffix.lower() in ['.yml', '.yaml']:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        elif config_path.suffix.lower() == '.json':
            json.dump(config, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def load_data(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    データファイルの読み込み（CSV, Excel, JSON対応）
    
    Args:
        file_path: ファイルパス
        **kwargs: pandas読み込み関数への追加引数
        
    Returns:
        DataFrame
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    suffix = file_path.suffix.lower()
    
    if suffix == '.csv':
        return pd.read_csv(file_path, **kwargs)
    elif suffix in ['.xlsx', '.xls']:
        return pd.read_excel(file_path, **kwargs)
    elif suffix == '.json':
        return pd.read_json(file_path, **kwargs)
    elif suffix == '.parquet':
        return pd.read_parquet(file_path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def save_data(data: pd.DataFrame, file_path: Union[str, Path], **kwargs) -> None:
    """
    データファイルの保存
    
    Args:
        data: 保存するDataFrame
        file_path: 保存先パス
        **kwargs: pandas保存関数への追加引数
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    suffix = file_path.suffix.lower()
    
    if suffix == '.csv':
        data.to_csv(file_path, index=False, **kwargs)
    elif suffix in ['.xlsx', '.xls']:
        data.to_excel(file_path, index=False, **kwargs)
    elif suffix == '.json':
        data.to_json(file_path, orient='records', force_ascii=False, **kwargs)
    elif suffix == '.parquet':
        data.to_parquet(file_path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def get_file_list(directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
    """
    ディレクトリ内のファイル一覧を取得
    
    Args:
        directory: 検索ディレクトリ
        pattern: ファイルパターン（glob形式）
        recursive: 再帰的に検索するかどうか
        
    Returns:
        ファイルパスのリスト
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


def get_project_root() -> Path:
    """
    プロジェクトルートディレクトリを取得
    
    Returns:
        プロジェクトルートのPath
    """
    current_path = Path(__file__).resolve()
    
    # requirements.txtまたは.gitがあるディレクトリを探す
    for parent in current_path.parents:
        if (parent / "requirements.txt").exists() or (parent / ".git").exists():
            return parent
    
    # 見つからない場合は現在のファイルの3つ上のディレクトリを返す
    return current_path.parents[2]


def main():
    """サンプル実行"""
    # プロジェクトルートの取得
    root = get_project_root()
    print(f"プロジェクトルート: {root}")
    
    # サンプル設定ファイルの作成
    config_dir = root / "config"
    ensure_dir(config_dir)
    
    sample_config = {
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed"
        },
        "processing": {
            "language": "japanese",
            "max_length": 1000
        }
    }
    
    config_path = config_dir / "config.yaml"
    save_config(sample_config, config_path)
    print(f"設定ファイルを作成しました: {config_path}")
    
    # 設定ファイルの読み込みテスト
    loaded_config = load_config(config_path)
    print(f"読み込まれた設定: {loaded_config}")


if __name__ == "__main__":
    main()