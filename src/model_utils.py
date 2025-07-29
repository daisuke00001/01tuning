# モデル関連ユーティリティ

import torch
from typing import Tuple, Optional
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    """モデル管理クラス"""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.tokenizer = None

    def load_model(self) -> Tuple[object, object]:
        try:
            from unsloth import FastLanguageModel
            logger.info(f"モデルを読込中: {self.config.model.name}")

            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.config.model.name,
                max_seq_length=self.config.model.max_seq_length,
                dtype=self.config.model.dtype,
                load_in_4bit=self.config.model.load_in_4bit,
                token=self.config.model.token,
            )

            self.model = model
            self.tokenizer = tokenizer
            logger.info("✅モデル読込完了")
            return model, tokenizer
        
        except Exception as e:
            logger.error(f"✖モデル読込エラー: {e}")
            raise

    def setup_lora(self) -> object:
        """LoRA設定"""
        if self.model is None:
            raise ValueError("モデルが読み込まれていません。load_model()を先に実行してください。")
        
        try:
            from unsloth import FastLanguageModel
            logger.info("LoRA設定を適用中...")
            self.model = FastLanguageModel.get_peft_lora(
                self.model,
                r=self.config.lora.r,
                target_modules=self.config.lora.target_modules,
                lora_alpha=self.config.lora.lora_alpha,
                lora_dropout=self.config.lora.lora_dropout,
                bias=self.config.lora.bias,
                use_gradient_checkpointing=self.config.lora.use_gradient_checkpointing,
                random_state=self.config.lora.random_state,
                use_rslora=self.config.lora.use_rslora,
                loftq_config=self.config.lora.loftq_config,
            )

            logger.info("✅ LoRA設定完了")
            return self.model
        
        except Exception as e:
            logger.error(f"✖LoRA設定セラー: {e}")
            raise

    def get_memory_stats(self) -> dict:
        """GPU メモリ使用量を取得"""
        if not torch.cuda.is_available():
            return {"error": "CUDA not available"}
        
        gpu_stats = torch.cuda.get_device_properties(0)
        reserved = torch.cuda.memory_reserved() / 1024 / 1024 / 1024 
        total = gpu_stats.total_memory / 1024 / 1024 / 1024

        return {
            "gpu_name": gpu_stats.name,
            "total_memory_gb": round(total, 3),
            "reserved_memory_gb": round(reserved, 3),
            "usage_percentage":round((reserved / total) * 100, 1)
        }
    
    def save_model(self, save_path: str):
        """モデルを保存"""
        if self.model is None or self.tokenizer is None:
            raise ValueError("モデルorトークナイザが読み込まれていません。")
        
        try:
            logger.info(f"モデルを保存中: {save_path}")

            self.model.save_pretrained(save_path)
            self.tokenizer.save_pretrained(save_path)

            logger.info("✅モデル保存完了")
            return True
        
        except Exception as e:
            logger.error(f"✖モデル保存エラー {e}")
            raise