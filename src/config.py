# config.py 設定管理モジュール

import yaml
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
import os

@dataclass
class ModelConfig:
    """モデル設定"""
    name: str = "SakanaAI/TinySwallow-1.5B-Instruct"
    max_seq_length: int = 2048
    dtype: Optional[str] = None
    load_in_4bit: bool = True
    token: Optional[str] = None

@dataclass
class LoraConfig:
    """LoRA設定"""
    r: int = 16
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    bias: str = "none"
    target_modules: List[str] = None
    use_gradient_checkpointing: str = "unsloth"
    random_state: int = 3407
    use_rslora: bool = False
    loftq_config: Optional[dict] = None

    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

@dataclass
class TrainingConfig:
    """トレーニング設定"""
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 4
    warmup_steps: int = 5
    max_steps: int = 60
    num_train_epochs: Optional[int] = None
    learning_rate: float = 2e-4
    logging_steps: int = 1
    optim: str = "adamw_8bit"
    weight_decay: float = 0.01
    lr_scheduler_type: str = "linear"
    seed: int = 3407
    output_dir: str ="outputs"
    report_to: str = "none"
    save_steps: Optional[int] = None
    save_total_limit: Optional[int] = None

@dataclass
class DataConfig:
    """データ設定"""
    dataset_name: str = "yahma/alpaca_cleand"
    train_split: str = "train"
    text_field: str = "text"
    dataset_num_proc: int = 2
    packing: bool = True

@dataclass
class Config:
    """統合設定"""
    model: ModelConfig 
    lora: LoraConfig
    training: TrainingConfig
    data: DataConfig

    @classmethod
    def load_from_yaml(cls, config_path: str):
        """YAMLファイルからの設定を読込"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

            return cls(
                model=ModelConfig(**config_dict.get('model', {})),
                lora=LoraConfig(**config_dict.get('lora', {})),
                training=TrainingConfig(**config_dict.get('training', {})),
                data=DataConfig(**config_dict.get('data', {}))
            )
        
    def save_yaml(self, config_path: str):
        """設定をYAMLファイルに保存"""
        config_dict = {
            'model': self.model.__dict__,
            'lora': self.lora.__dict__,
            'training': self.training.__dict__,
            'data': self.data.__dict__
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            