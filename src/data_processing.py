# データ前処理モジュール
from datasets import load_dataset, Dataset
from typing import Dict, List, Any
import logging
from config import Config

logger = logging.getLogger(__name__)

class DataProcessor:
    """データ処理クラス"""

    def __init__(self, config: Config, tokenizer=None):
        self.config = config
        self.tokenizer = tokenizer
        self.dataset = None

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
        
