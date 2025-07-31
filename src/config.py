# config.py 設定管理モジュール

import yaml
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
import os

@dataclass
class ModelConfig:
    """モデル設定"""
    name: str = "SakanaAI/TinySwallow-1.5B-Instruct"
    model_type: Optional[str] = None
    tokenizer_name: Optional[str] = None
    use_fast_tokenizer: bool = True
    trust_remote_code: bool = False
    max_seq_length: int = 2048
    dtype: Optional[str] = None
    load_in_4bit: bool = True
    token: Optional[str] = None

@dataclass
class LoraConfig:
    """LoRA設定"""
    r: int = 16
    alpha: int = 16  # YAMLでは 'alpha' で指定
    lora_alpha: int = 16  # 下位互換性のため残す
    dropout: float = 0.05  # YAMLでは 'dropout' で指定
    lora_dropout: float = 0.05  # 下位互換性のため残す
    bias: str = "none"
    target_modules: List[str] = None
    task_type: str = "CAUSAL_LM"
    use_gradient_checkpointing: str = "unsloth"
    random_state: int = 3407
    use_rslora: bool = False
    loftq_config: Optional[dict] = None
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        # alpha と lora_alpha の同期
        if hasattr(self, 'alpha') and self.alpha != self.lora_alpha:
            self.lora_alpha = self.alpha
        # dropout と lora_dropout の同期  
        if hasattr(self, 'dropout') and self.dropout != self.lora_dropout:
            self.lora_dropout = self.dropout

@dataclass
class TrainingConfig:
    """トレーニング設定"""
    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: Optional[int] = None
    gradient_accumulation_steps: int = 4
    warmup_steps: int = 5
    warmup_ratio: Optional[float] = None
    max_steps: int = 60
    num_train_epochs: Optional[int] = None
    learning_rate: float = 2e-4
    logging_steps: int = 1
    eval_steps: Optional[int] = None
    optim: str = "adamw_8bit"
    weight_decay: float = 0.01
    lr_scheduler_type: str = "linear"
    seed: int = 3407
    output_dir: str ="outputs"
    report_to: str = "none"
    save_steps: Optional[int] = None
    save_total_limit: Optional[int] = None
    load_best_model_at_end: bool = False
    metric_for_best_model: Optional[str] = None
    greater_is_better: bool = False

@dataclass
class DatasetConfig:
    """データセット設定"""
    name: str = "alpaca_japanese"
    format: str = "alpaca"
    instruction_template: str = "以下の指示に従ってください。\n\n### 指示:\n{instruction}\n\n### 応答:\n"
    response_template: str = "{output}"
    # 特許データ用フィールド
    data_files: Optional[Dict[str, str]] = None
    auto_discovery: bool = False
    discovery_paths: Optional[List[str]] = None
    supported_formats: Optional[List[str]] = None
    max_patent_length: int = 2048
    max_implementation_length: int = 1024
    remove_references: bool = True
    clean_formatting: bool = True

@dataclass
class QuantizationConfig:
    """量子化設定"""
    load_in_4bit: bool = True
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_compute_dtype: str = "float16"

@dataclass
class UnslothConfig:
    """Unsloth設定"""
    use_unsloth: bool = True
    max_seq_length: int = 2048
    dtype: Optional[str] = None
    load_in_4bit: bool = True

@dataclass
class DataConfig:
    """データ設定（下位互換性のため）"""
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
    dataset: Optional[DatasetConfig] = None
    quantization: Optional[QuantizationConfig] = None
    unsloth: Optional[UnslothConfig] = None
    data: Optional[DataConfig] = None  # 下位互換性のため

    @classmethod
    def load_from_yaml(cls, config_path: str):
        """YAMLファイルからの設定を読込"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

            return cls(
                model=ModelConfig(**config_dict.get('model', {})),
                lora=LoraConfig(**config_dict.get('lora', {})),
                training=TrainingConfig(**config_dict.get('training', {})),
                dataset=DatasetConfig(**config_dict.get('dataset', {})) if 'dataset' in config_dict else None,
                quantization=QuantizationConfig(**config_dict.get('quantization', {})) if 'quantization' in config_dict else None,
                unsloth=UnslothConfig(**config_dict.get('unsloth', {})) if 'unsloth' in config_dict else None,
                data=DataConfig(**config_dict.get('data', {})) if 'data' in config_dict else None
            )
        
    def save_yaml(self, config_path: str):
        """設定をYAMLファイルに保存"""
        config_dict = {
            'model': self.model.__dict__,
            'lora': self.lora.__dict__,
            'training': self.training.__dict__,
        }
        
        if self.dataset:
            config_dict['dataset'] = self.dataset.__dict__
        if self.quantization:
            config_dict['quantization'] = self.quantization.__dict__
        if self.unsloth:
            config_dict['unsloth'] = self.unsloth.__dict__
        if self.data:
            config_dict['data'] = self.data.__dict__
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            