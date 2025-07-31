# トレーニング関連ユーティリティ

from trl import SFTConfig, SFTTrainer
import logging
from config import Config

logger = logging.getLogger(__name__)

class TrainingManager:
    """トレーニング管理クラス"""

    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.training_stats = None
        
    def format_chatml_messages(self, example):
        """ChatML形式のmessagesを単一テキストに変換（リスト形式で返す）"""
        try:
            if 'messages' in example:
                # messagesを単一のテキストに結合
                text_parts = []
                for message in example['messages']:
                    # メッセージの形式を確認して適切に処理
                    if isinstance(message, dict):
                        # 辞書形式: {"role": "user", "content": "..."}
                        role = message.get('role', '')
                        content = message.get('content', '')
                    elif isinstance(message, list) and len(message) >= 2:
                        # リスト形式: ["user", "content"]
                        role = str(message[0]) if message[0] else ''
                        content = str(message[1]) if message[1] else ''
                    elif isinstance(message, str):
                        # 文字列形式: 全体をcontentとして扱う
                        role = 'unknown'
                        content = message
                    else:
                        # その他の形式: 文字列に変換
                        role = 'unknown'
                        content = str(message)
                    
                    text_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
                
                # Unslothは文字列のリストを期待しているため、リストで返す
                return ["\n".join(text_parts)]
            elif 'text' in example:
                # 既にtextフィールドがある場合はリスト形式で返す
                return [example['text']]
            else:
                # どちらもない場合は空文字列をリスト形式で返す
                return [""]
        except Exception as e:
            # エラーが発生した場合のフォールバック
            logger.error(f"formatting_funcでエラー発生: {e}, example keys: {list(example.keys()) if isinstance(example, dict) else type(example)}")
            return [str(example)]
        
    def create_trainer(self, model, tokenizer, dataset) -> SFTTrainer:
        """トレーナーを作成"""
        try:
            logger.info("トレーナーを設定中...")

            # SFTConfig 設定（型変換を確実にする）
            sft_config = SFTConfig(
                per_device_train_batch_size=int(self.config.training.per_device_train_batch_size),
                gradient_accumulation_steps=int(self.config.training.gradient_accumulation_steps),
                warmup_steps=int(self.config.training.warmup_steps),
                max_steps=int(self.config.training.max_steps),
                learning_rate=float(self.config.training.learning_rate),
                logging_steps=int(self.config.training.logging_steps),
                optim=str(self.config.training.optim),
                weight_decay=float(self.config.training.weight_decay),
                lr_scheduler_type=str(self.config.training.lr_scheduler_type),
                seed=int(self.config.training.seed),
                output_dir=str(self.config.training.output_dir),
                report_to=str(self.config.training.report_to),
            )

            # save_steps と save_total_limitが設定されている場合は追加（型変換付き）
            if self.config.training.save_steps is not None:
                sft_config.save_steps = int(self.config.training.save_steps)
            if self.config.training.save_total_limit is not None:
                sft_config.save_total_limit = int(self.config.training.save_total_limit)

            # データセットの形式を確認
            sample_data = dataset[0] if len(dataset) > 0 else {}
            
            # データ構造をデバッグ出力
            if len(dataset) > 0:
                logger.info(f"データセットサンプル構造: {list(sample_data.keys())}")
                if 'messages' in sample_data:
                    messages = sample_data['messages']
                    logger.info(f"messages構造: {type(messages)}, 長さ: {len(messages) if hasattr(messages, '__len__') else 'N/A'}")
                    if len(messages) > 0:
                        first_message = messages[0]
                        logger.info(f"最初のmessage構造: {type(first_message)}, 内容: {first_message if len(str(first_message)) < 200 else str(first_message)[:200]+'...'}")
            
            # ChatML形式の場合はformatting_funcを使用
            if 'messages' in sample_data:
                logger.info("ChatML形式のデータセットを検出、formatting_funcを使用します")
                trainer = SFTTrainer(
                    model=model,
                    tokenizer=tokenizer,
                    train_dataset=dataset,
                    formatting_func=self.format_chatml_messages,
                    max_seq_length=self.config.model.max_seq_length,
                    dataset_num_proc=self.config.data.dataset_num_proc,
                    packing=self.config.data.packing,
                    args=sft_config,
                )
            else:
                # 通常のテキスト形式の場合はdataset_text_fieldを使用
                logger.info("通常のテキスト形式のデータセットを使用します")
                trainer = SFTTrainer(
                    model=model,
                    tokenizer=tokenizer,
                    train_dataset=dataset,
                    dataset_text_field=self.config.data.text_field,
                    max_seq_length=self.config.model.max_seq_length,
                    dataset_num_proc=self.config.data.dataset_num_proc,
                    packing=self.config.data.packing,
                    args=sft_config,
                )

            self.trainer = trainer
            logger.info("✅トレーナー作成完了")
            return trainer
        
        except Exception as e:
            logger.error(f"✖トレーナー設定エラー: {e}")
            raise

    def train(self) -> dict:
        """トレーニングを実行"""
        if self.trainer is None:
            raise ValueError("トレーナーが設定されていません。create_trainer()を先に実行してください。")
        
        try:
            logger.info("🚀トレーニングを開始...")

            self.training_stats = self.trainer.train()
            logger.info("✅トレーニング完了")
            return self.training_stats
        
        except Exception as e:
            logger.error(f"✖トレーニングエラー: {e}")
            raise

    def get_training_summary(self) -> dict:
        """トレーニング結果のサマリーを取得"""
        if self.training_stats is None:
            return {"error": "トレーニングが実行されていません"}
        
        runtime = self.training_stats.metrics.get('train_runtime', 0)

        return {
            "train_runtime_seconds": round(runtime, 1),
            "train_runtime_minutes": round(runtime / 60, 2),
            "train_samples_per_second": self.training_stats.metrics.get('train_samples_per_second', 0),
            "train_steps_per_second": self.training_stats.metrics.get('train_steps_per_second', 0),
            "total_flos": self.training_stats.metrics.get('total_flos', 0),
            "train_loss": self.training_stats.metrics.get('train_loss', 0),
        }