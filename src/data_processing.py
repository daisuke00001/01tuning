# データ前処理モジュール
from datasets import load_dataset, Dataset
from typing import Dict, List, Any
import logging

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
    
    def formatting_prompts_func(self, example: Dict[str, List]) -> Dict[str, List[str]]:
        """データをAlpacaフォーマットに変換"""
        if self.tokenizer is None:
            raise ValueError("トークナイザーが設定されていません")
        
        alpaca_prompt = self.create_alpaca_prompt_template()
        EOS_TOKEN = self.tokenizer.eos_token

        instruction = example["instruction"]
        inputs = example["input"]
        outputs = example["output"]
        texts = []

        for instruction, input_text, output in zip(instruction, inputs, outputs):
            text = alpaca_prompt.format(instruction, input_text, output)
            texts.append(text)

        return texts
    
    def load_and_process_dataset(self) -> Dataset:
        """データセット読込、前処理を実行"""
        try:
            logger.info("データセットを読込中: {self.config.data.dataset_name}")
            
            dataset = load_dataset(
                self.config.data.dataset_name,
                split=self.config.data.train_split
            )

            logger.info("✅データセット読込完了")
        
            # データを前処理
            dataset = dataset.map(
                self.formatting_prompts_func,
                batched=True,
                num_proc=self.config.data.dataset_num_proc
            )

            self.dataset = dataset
            logger.info("✅データ前処理完了")
            return dataset
        
        except Exception as e:
            logger.error(f"✖データ処理エラー: {e}")
            raise
        
