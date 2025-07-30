# 推論関連ユーティリティ

import torch
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class InferenceManager:
    """推論管理クラス"""

    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self._setup_inference()

    def _setup_inference(self):
        """推論モードをセットアップ"""
        try:
            # モデルを推論モードに設定
            self.model.eval()
            logger.info("✅推論モードセットアップ完了")
        except Exception as e:
            logger.error(f"✖推論モード設定エラー: {e}")

    def generate_response(
            self,
            prompt: str,
            max_new_tokens: int = 64,
            temperature: float = 0.7,
            do_sample: bool = True,
            top_p: float = 0.9,
            repetition_penalty: float = 1.1,
    ) -> str:
        """応答を生成"""
        try:
            # プロンプトをトークン化
            inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")

            # 生成実行
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    use_cache=True,
                    do_sample=do_sample,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    eos_token_id=self.tokenizer.eos_token_id,
                    pad_token_id=self.tokenizer.pad_token_id,
                )

            # 応答をデコード
            response = self.tokenizer.batch_decode(outputs)[0]

            return response
        
        except Exception as e:
            logger.error(f"✖生成エラー: {e}")
            raise

    def test_alpaca_format(self, instruction: str, input_text: str = "") -> str:
        """Alpacaフォーマットでのテスト生成"""
        alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

        ### Instruction:
        {}

        ### Input:
        {}

        ### Response:
        {}
        """
        prompt = alpaca_prompt.format(instruction, input_text, "")
        return self.generate_response(prompt)
