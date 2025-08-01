# データ前処理モジュール
from datasets import load_dataset, Dataset
from typing import Dict, List, Any
import logging
from .config import Config

# 特許データ処理モジュールをインポート
try:
    from .patent_processing.text_processor import PatentTextProcessor
    from .utils.data_discovery import DataDiscovery
    PATENT_PROCESSING_AVAILABLE = True
except ImportError:
    PATENT_PROCESSING_AVAILABLE = False
    
logger = logging.getLogger(__name__)

class DataProcessor:
    """データ処理クラス"""

    def __init__(self, config: Config, tokenizer=None):
        self.config = config
        self.tokenizer = tokenizer
        self.dataset = None
        
    def clean_patent_text(self, text: str) -> str:
        """特許テキストのクリーニング"""
        import re
        
        if not isinstance(text, str):
            return ""
        
        # 異常な文字列パターンを除去
        text = re.sub(r'CHEMICAL\d+', '', text)  # CHEMICAL6479等を除去
        text = re.sub(r'LEGAL\d+', '', text)     # LEGAL170等を除去
        text = re.sub(r'MIC[A-Z]*', '', text)    # MICA等を除去
        text = re.sub(r'CH{3,}', '', text)       # CHCHCHCH等を除去
        text = re.sub(r'AL\d+', '', text)        # AL20等を除去
        
        # 連続する同じ文字を除去（3文字以上）
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        # 複数の空白を単一に
        text = re.sub(r'\s+', ' ', text)
        
        # 制御文字を除去
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
        
    def limit_text_length(self, text: str, max_length: int = 2000) -> str:
        """テキスト長を制限"""
        if len(text) > max_length:
            # 文の区切りで切る
            sentences = text.split('。')
            result = ""
            for sentence in sentences:
                if len(result + sentence + '。') <= max_length:
                    result += sentence + '。'
                else:
                    break
            return result if result else text[:max_length]
        return text
        
        # 特許データ処理機能の初期化
        if PATENT_PROCESSING_AVAILABLE:
            self.patent_processor = PatentTextProcessor(language="japanese")
            self.data_discovery = DataDiscovery()
            logger.info("✅特許データ処理機能が利用可能です")
        else:
            self.patent_processor = None
            self.data_discovery = None
            logger.warning("⚠️特許データ処理機能は利用できません")

    def create_alpaca_prompt_template(self) -> str:
        """Alpaca プロンプトテンプレートを作成"""
        return """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

        ### Instruction:
        {}

        ### Input:
        {}

        ### Response:
        {}
        """
    
    def formatting_prompts_func(self, examples: Dict[str, List]) -> Dict[str, List[str]]:
        """データをAlpacaフォーマットに変換"""
        if self.tokenizer is None:
            raise ValueError("トークナイザーが設定されていません")
        
        alpaca_prompt = self.create_alpaca_prompt_template()
        EOS_TOKEN = self.tokenizer.eos_token

        instructions = examples.get("instruction", examples.get("text", [""] * len(list(examples.values())[0])))
        inputs = examples.get("input", [""] * len(instructions))
        outputs = examples.get("output", examples.get("response", [""] * len(instructions)))
        
        texts = []
        for instruction, input_text, output in zip(instructions, inputs, outputs):
            text = alpaca_prompt.format(instruction, input_text, output) + EOS_TOKEN
            texts.append(text)

        return {"text": texts}
    
    def create_dummy_dataset(self, size: int = 100) -> Dataset:
        """ダミーデータセットを作成（デモ・テスト用）"""
        logger.info(f"ダミーデータセット作成中 (サイズ: {size})")
        
        dummy_data = {
            "instruction": [
                "以下の文章を要約してください。",
                "次の質問に答えてください。",
                "フィボナッチ数列を続けてください。",
                "日本の首都を教えてください。",
                "簡単な自己紹介をしてください。"
            ] * (size // 5 + 1),
            "input": [
                "人工知能は様々な分野で活用されています。",
                "日本で最も高い山は何ですか？",
                "1, 1, 2, 3, 5, 8",
                "",
                ""
            ] * (size // 5 + 1),
            "output": [
                "AIは多分野で利用されています。",
                "富士山です。",
                "13, 21, 34",
                "東京です。",
                "私はAIアシスタントです。"
            ] * (size // 5 + 1)
        }
        
        # サイズ調整
        for key in dummy_data:
            dummy_data[key] = dummy_data[key][:size]
        
        return Dataset.from_dict(dummy_data)

    def load_and_process_dataset(self) -> Dataset:
        """データセット読込、前処理を実行"""
        try:
            logger.info(f"データセットを読込中: {self.config.data.dataset_name}")
            
            # データセット読み込み試行
            try:
                dataset = load_dataset(
                    self.config.data.dataset_name,
                    split=self.config.data.train_split
                )
                logger.info("✅データセット読込完了")
            except Exception as dataset_error:
                logger.warning(f"⚠️ データセット読込失敗: {dataset_error}")
                logger.info("ダミーデータセットを使用します")
                dataset = self.create_dummy_dataset(size=50)
        
            # データを前処理
            logger.info("データを前処理中...")
            dataset = dataset.map(
                self.formatting_prompts_func,
                batched=True,
                num_proc=self.config.data.dataset_num_proc
            )

            self.dataset = dataset
            logger.info(f"✅データ前処理完了 (サンプル数: {len(dataset)})")
            return dataset
        
        except Exception as e:
            logger.error(f"✖データ処理エラー: {e}")
            raise

    def load_patent_dataset(self, data_path: str = None) -> Dataset:
        """特許データセットを読み込み、前処理を実行"""
        if not PATENT_PROCESSING_AVAILABLE:
            raise RuntimeError("特許データ処理機能が利用できません。依存関係を確認してください。")
            
        try:
            # データディスカバリーまたは指定パスから読み込み
            if data_path is None:
                logger.info("自動データディスカバリーを実行中...")
                xml_dirs = self.data_discovery.discover_xml_directories()
                
                # XMLファイルを探す優先順位: JPB発行分 > raw_data > その他
                discovered_files = []
                for dir_type in ['jpb_release', 'raw_data', 'single_files', 'bulk_processing']:
                    for dir_path in xml_dirs.get(dir_type, []):
                        xml_files = list(dir_path.glob("**/*.xml"))
                        if xml_files:
                            discovered_files.extend(xml_files)
                            break
                    if discovered_files:
                        break
                
                if not discovered_files:
                    raise ValueError("特許XMLファイルが見つかりませんでした")
                data_path = str(discovered_files[0])  # 最初に見つかったXMLファイルを使用
                
            logger.info(f"特許データを読み込み中: {data_path}")
            
            # 特許データの処理
            if data_path.endswith('.xml'):
                # XML ファイルの処理
                processed_data = self.patent_processor.parse_xml_file(data_path)
                # parse_xml_fileは辞書を返すので、リスト形式に変換
                if isinstance(processed_data, dict):
                    processed_data = [processed_data]
            elif data_path.endswith('.json') or data_path.endswith('.jsonl'):
                # JSONファイルの処理
                import json
                processed_data = []
                
                try:
                    # 文字化け対策のため複数のエンコーディングを試行
                    encodings = ['utf-8', 'cp932', 'shift_jis', 'utf-8-sig']
                    
                    for encoding in encodings:
                        try:
                            if data_path.endswith('.json'):
                                # JSON形式
                                with open(data_path, 'r', encoding=encoding) as f:
                                    data = json.load(f)
                                    if isinstance(data, list):
                                        processed_data = data
                                    else:
                                        processed_data = [data]
                                break
                            else:
                                # JSONL形式
                                with open(data_path, 'r', encoding=encoding) as f:
                                    for line in f:
                                        line = line.strip()
                                        if line:
                                            processed_data.append(json.loads(line))
                                break
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            continue
                    
                    if not processed_data:
                        logger.error(f"JSONファイルの読み込みに失敗: {data_path}")
                        processed_data = [{"error": f"JSONファイルの読み込みに失敗: {data_path}"}]
                    else:
                        logger.info(f"JSONファイル読み込み成功: {len(processed_data)}件のデータ")
                        
                        # 特許データのクリーニング処理
                        logger.info("特許データクリーニング開始...")
                        cleaned_data = []
                        for item in processed_data:
                            if isinstance(item, dict):
                                cleaned_item = {}
                                for key, value in item.items():
                                    if key == 'text' and isinstance(value, str):
                                        # テキストフィールドをクリーニング
                                        cleaned_text = self.clean_patent_text(value)
                                        cleaned_text = self.limit_text_length(cleaned_text, 1500)
                                        cleaned_item[key] = cleaned_text
                                    elif isinstance(value, str):
                                        # その他の文字列フィールドも軽くクリーニング
                                        cleaned_item[key] = self.clean_patent_text(value)[:500]
                                    else:
                                        cleaned_item[key] = value
                                
                                # 有効なデータのみ保持
                                if cleaned_item.get('text') and len(cleaned_item['text']) > 100:
                                    cleaned_data.append(cleaned_item)
                        
                        processed_data = cleaned_data
                        logger.info(f"クリーニング完了: {len(processed_data)}件の有効データ")
                        
                except Exception as e:
                    logger.error(f"JSON処理エラー: {e}")
                    processed_data = [{"error": f"JSON処理エラー: {e}"}]
            else:
                raise ValueError(f"サポートされていないファイル形式: {data_path}")
            
            # Datasetで期待される形式に変換
            if isinstance(processed_data, list) and len(processed_data) > 0:
                # 辞書のリストをDatasetで使える形式に変換
                dataset_dict = {}
                for key in processed_data[0].keys():
                    dataset_dict[key] = [item.get(key, "") for item in processed_data]
                processed_data = dataset_dict
            
            # Datasetオブジェクトに変換
            dataset = Dataset.from_dict(processed_data)
            
            # トークナイザーが指定されている場合は前処理を実行
            if self.tokenizer is not None:
                dataset = dataset.map(
                    self.formatting_prompts_func,
                    batched=True,
                    num_proc=self.config.data.dataset_num_proc if self.config.data else 2
                )
            
            self.dataset = dataset
            logger.info(f"✅特許データ処理完了 (サンプル数: {len(dataset)})")
            return dataset
            
        except Exception as e:
            logger.error(f"✖特許データ処理エラー: {e}")
            raise

    def create_patent_training_dataset(self, data_format: str = "chatml") -> Dataset:
        """特許データから学習用データセットを作成"""
        if not PATENT_PROCESSING_AVAILABLE:
            raise RuntimeError("特許データ処理機能が利用できません。")
            
        try:
            # 特許データの読み込み
            if self.dataset is None:
                self.load_patent_dataset()
            
            logger.info(f"学習用データセット作成中 (フォーマット: {data_format})")
            
            if data_format == "chatml":
                # ChatMLフォーマットでの変換（利用可能なメソッドを使用）
                if hasattr(self.patent_processor, 'create_chatml_dataset'):
                    # DatasetをDataFrameに変換
                    import pandas as pd
                    df = pd.DataFrame([self.dataset[i] for i in range(len(self.dataset))])
                    # 出力ディレクトリ作成
                    from pathlib import Path
                    output_dir = Path("data/processed")
                    output_dir.mkdir(exist_ok=True)
                    training_dataset = self.patent_processor.create_chatml_dataset(df, str(output_dir))
                elif hasattr(self.patent_processor, 'create_training_dataset'):
                    # DataFrameに変換してからtraining_datasetを作成
                    import pandas as pd
                    df = pd.DataFrame([self.dataset[i] for i in range(len(self.dataset))])
                    self.patent_processor.create_training_dataset(df, "data/processed")
                    # 作成されたファイルから読み込み
                    import json
                    with open("data/processed/complete_dataset.json", "r", encoding="utf-8") as f:
                        training_data = json.load(f)
                    training_dataset = Dataset.from_dict(training_data)
                else:
                    # 基本的なフォーマット変換
                    training_data = {
                        "text": [],
                        "source": []
                    }
                    for i in range(len(self.dataset)):
                        item = self.dataset[i]
                        text = f"特許: {item.get('title', '')}\n要約: {item.get('abstract', '')}\nクレーム: {item.get('claims', '')}"
                        training_data["text"].append(text)
                        training_data["source"].append("patent")
                    training_dataset = Dataset.from_dict(training_data)
            elif data_format == "alpaca":
                # Alpacaフォーマットでの変換
                training_data = {
                    "instruction": [],
                    "input": [],
                    "output": []
                }
                for i in range(len(self.dataset)):
                    item = self.dataset[i]
                    training_data["instruction"].append("以下の特許文書の内容を要約してください。")
                    training_data["input"].append(f"タイトル: {item.get('title', '')}\n詳細: {item.get('detailed_description', '')}")
                    training_data["output"].append(item.get('abstract', ''))
                training_dataset = Dataset.from_dict(training_data)
            else:
                raise ValueError(f"サポートされていないフォーマット: {data_format}")
            
            logger.info(f"✅学習用データセット作成完了 (サンプル数: {len(training_dataset)})")
            return training_dataset
            
        except Exception as e:
            logger.error(f"✖学習用データセット作成エラー: {e}")
            raise
        
