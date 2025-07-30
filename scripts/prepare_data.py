"""
データ準備スクリプト
各種データセットのダウンロード、前処理、サンプル作成を行う    
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from typing import List, Dict, Any,Optional
import logging
from datasets import load_dataset, Dataset
import pandas as pd

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataPreparer:
    """データ準備クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "configs/tinyswallow_config.yaml"
        self.config = self._load_config()
        self.data_dir = Path("data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.samples_dir = self.data_dir / "samples"
        
        # ディレクトリ作成
        self._create_directories()
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            return self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            'data':{
            'dataset_name': 'tinyswallow',
            'train_split': 'train',
            'text_field': 'text',
            'dataset_num_proc': 2
            }
        }
        
    def _create_directories(self):
        """必要なディレクトリを作成"""
        for directory in [self.data_dir, self.raw_dir, self.processed_dir, self.samples_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁ディレクトリ作成: {directory}")
            
    def download_alpaca_dataset(self) -> bool:
        """Alpacaデータセットをダウンロード"""
        try:
            dataset_name = self.config['data']['dataset_name']
            dataset = load_dataset(dataset_name, split=self.config['data']['train_split'])
            
            # JSONファイルとして保存
            output_path = self.raw_dir / "alpaca_dataset.json"
            dataset.to_json(output_path)
            
            logger.info(f"✅ Alpacaデータセットを保存: {output_path}")
            logger.info(f"📊 サンプル数: {len(dataset):,}件")
            
            return True
        except Exception as e:
            logger.error(f"❌ Alpacaデータセットのダウンロードに失敗: {e}")
            return False
        
    def create_sample_dataset(self) -> bool:
        """サンプルデータセットを作成"""
        logger.info("📊 サンプルデータセットを作成中...")
        
        success = True
        
        # 基本的なAlpacaサンプル
        if not self._create_basic_alpaca_samples():
            success = False
            
        # 特許データサンプル
        if not self._create_patent_samples():
            success = False
            
        # カスタムサンプル
        if not self._create_custom_samples():
            success = False
            
        return success
    
    def _create_basic_alpaca_samples(self) -> bool:
        """Alpacaサンプルを作成"""
        try:
            sample_data = [
                {
                    "instruction": "次の数列を続けてください。",
                    "input": "2, 4, 6, 8",
                    "output": "10, 12, 14, 16です。これは偶数の数列で、各項は前の項に2を加えたものです。"
                },
                {
                    "instruction": "以下の文章を日本語に翻訳してください。",
                    "input": "Hello, how are you today?",
                    "output": "こんにちは、今日はいかがお過ごしですか？"
                },
                {
                    "instruction": "次の都市の首都を教えてください。",
                    "input": "フランス",
                    "output": "フランスの首都はパリです。"
                },
                {
                    "instruction": "簡単なPythonコードを書いてください。",
                    "input": "1から10までの数字を出力する",
                    "output": "```python\nfor i in range(1, 11):\n    print(i)\n```"
                },
                {
                    "instruction": "次の数学問題を解いてください。",
                    "input": "x + 5 = 12のxを求めよ",
                    "output": "x = 12 - 5 = 7です。"
                }           
            ]
            
            output_path = self.samples_dir / "alpaca_samples.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Alpacaサンプルを保存: {output_path}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Alpacaサンプルの作成に失敗: {e}")
            return False
        
    def _create_patent_samples(self) -> bool:
        """特許データのサンプルを作成"""
        try:
            patent_data = [
                {
                    "instruction": "化学特許の発明を実施するための形態の段落【0012】を作成してください",
                    "input": """【請求項1】
                    下記一般式（１）で表される化合物。
                    【化１】000001
                    ［一般式（１）において、Ｘ１およびＸ２は、一方がＮを表し、他方がＣ－Ｙ３を表す。Ｙ１～Ｙ３は１個がシアノ基を表し、残りの２個が各々独立に置換もしくは無置換のアリール基、または置換もしくは無置換のヘテロアリール基を表す。］""",
                    "output": """【0012】本発明の一般式（１）で表される化合物の具体的な合成例について説明する。まず、市販のベンゾニトリル（１ｇ、9.7ｍｍｏｌ）をジメチルホルムアミド（ＤＭＦ）20ｍＬに溶解し、炭酸カリウム（２ｇ、14.5ｍｍｏｌ）を加えて80℃で２時間撹拌する。この反応により、一般式（１）においてＹ１がシアノ基、Ｙ２およびＹ３がフェニル基である化合物を収率78％で得ることができる。生成物は白色結晶として単離され、融点は156-158℃である。"""
                },
                {
                    "instruction": "機械特許の実施形態段落【0015】を作成してください",
                    "input": """【請求項1】
                    基板と、前記基板上に設けられた回転軸と、前記回転軸に取り付けられた回転体とを備えた回転装置。""",
                    "output": """【0015】図１に示すように、本実施形態の回転装置10は、基板11、回転軸12、および回転体13を主要な構成要素として備えている。基板11は、アルミニウム合金製の平板状部材であり、厚さ5mmの板材を使用している。回転軸12は、基板11の中央部に垂直に取り付けられており、ステンレス鋼（SUS304）製で直径10mm、長さ50mmの円柱状である。回転体13は、回転軸12の上端に固定され、直径100mmの円盤状に形成されている。"""
                },
                {
                    "instruction": "ソフトウェア特許の実施形態段落【0018】を作成してください",
                    "input": """【請求項1】
                    データを受信する受信部と、受信したデータを処理する処理部と、処理結果を出力する出力部とを備えた情報処理装置。""",
                    "output": """【0018】図３に示すように、本実施形態の情報処理装置30は、受信部31、処理部32、および出力部33から構成される。受信部31は、ネットワークインターフェース（NIC）を介してTCP/IP プロトコルによりデータを受信する。受信されるデータは、JSON形式またはXML形式のテキストデータであり、最大1MBまでのサイズに対応している。処理部32は、CPU（Intel Core i7-9700K）とメモリ（DDR4 16GB）を用いて、受信データの解析および所定のアルゴリズムに基づく演算処理を実行する。"""
                }
            ]
            
            output_path = self.samples_dir / "patent_samples.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(patent_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ 特許データのサンプルを保存: {output_path}")
                return True
            
        except Exception as e:
            logger.error(f"❌ 特許データのサンプルの作成に失敗: {e}")
            return False
        
    def _create_custom_samples(self) -> bool:
        """カスタムタスク用サンプルを作成"""
        try:
            custom_data = [
                {
                    "instruction": "以下のテキストを要約してください。",
                    "input": "人工知能（AI）技術は急速に発展しており、特に大規模言語モデル（LLM）は自然言語処理の分野で革命的な進歩をもたらしています。これらのモデルは、テキスト生成、翻訳、質問応答、コード生成など、様々なタスクで人間レベルまたはそれを超える性能を示しています。しかし、計算コストの高さやバイアスの問題など、解決すべき課題も多く存在します。",
                    "output": "AI技術、特に大規模言語モデル（LLM）は自然言語処理で革命的進歩を遂げ、多様なタスクで優秀な性能を示していますが、計算コストやバイアスなどの課題が残存しています。"
                },
                {
                    "instruction": "次のデータから傾向を分析してください。",
                    "input": "売上データ: 1月:100万円, 2月:120万円, 3月:110万円, 4月:140万円, 5月:160万円",
                    "output": "売上データの分析結果：全体的に上昇傾向を示しており、1月から5月にかけて60万円（60%）の増加が見られます。3月に一時的な減少がありましたが、4月以降は安定した成長を継続しています。月平均成長率は約15%です。"
                },
                {
                    "instruction": "プログラミングの問題を解いてください。",
                    "input": "リスト[1, 2, 3, 4, 5]の各要素を2倍にして新しいリストを作成するPythonコードを書いてください。",
                    "output": "```python\n# 方法1: リスト内包表記を使用\noriginal_list = [1, 2, 3, 4, 5]\ndoubled_list = [x * 2 for x in original_list]\nprint(doubled_list)  # [2, 4, 6, 8, 10]\n\n# 方法2: map関数を使用\ndoubled_list2 = list(map(lambda x: x * 2, original_list))\nprint(doubled_list2)  # [2, 4, 6, 8, 10]\n```"
                }
            ]
            
            output_path = self.samples_dir / "custom_samples.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(custom_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ カスタムサンプル作成完了: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ カスタムサンプル作成失敗: {e}")
            return False
            
    def validate_data_format(self, data_path: str) -> bool:
        """データフォーマットの検証"""
        logger.info(f"🔍データフォーマットを検証中: {data_path}")
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                logger.error(f"❌ データはリスト形式である必要があります")
                return False
            
            required_fields = ['instruction', 'input', 'output']
            
            for i, item in enumerate(data[:5]):
                if not isinstance(item, dict):
                    logger.error(f"❌ アイテム{i}は辞書形式である必要があります")
                    return False
                
                for field in required_fields:
                    if field not in item:
                        logger.error(f"❌ アイテム{i}に{field}フィールドがありません")
                        return False
                    
                    if not isinstance(item[field], str):
                        logger.error(f"❌ アイテム{i}の{field}フィールドは文字列である必要があります")
                        return False
                    
            logger.info(f"✅ データフォーマットの検証完了:  {len(data)}件のアイテム")
            return True
        
        except Exception as e:
            logger.error(f"❌ データフォーマットの検証に失敗: {e}")
            return False
        
    def create_data_statistics(self) -> bool:
        """データ統計を作成"""
        logger.info("📊 データ統計を作成中...")
        
        try:
            statistics = {}
            
            # 各サンプルファイルの統計を作成
            sample_files = list(self.samples_dir.glob("*.json"))
            
            for sample_file in sample_files:
                with open(sample_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    stats = {
                        'total_samples': len(data),
                        'avg_instruction_length': sum(len(item['instruction']) for item in data) / len(data),
                        'avg_input_length': sum(len(item['input']) for item in data) / len(data),
                        'avg_output_length': sum(len(item['output']) for item in data) / len(data),
                        'max_instruction_length': max(len(item['instruction']) for item in data),
                        'max_input_length': max(len(item['input']) for item in data),
                        'max_output_length': max(len(item['output']) for item in data)                                    
                    }
                    
                    statistics[sample_file.stem] = stats
                    
            # 統計をファイルに保存
            stats_path = self.processed_dir / "data_statistics.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2)
                
            # コンソールに表示
            print("\n📊 データ統計:")
            print("-" * 50)
            for dataset_name, stats in statistics.items():
                print(f"\n📁 {dataset_name}:")
                print(f"  サンプル数: {stats['total_samples']}")
                print(f"  平均指示長: {stats['avg_instruction_length']:.1f}文字")
                print(f"  平均入力長: {stats['avg_input_length']:.1f}文字")
                print(f"  平均出力長: {stats['avg_output_length']:.1f}文字")
            
            logger.info(f"✅ データ統計作成完了: {stats_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ データ統計作成失敗: {e}")
            return False
        
    def run_full_preparation(self) -> bool:
        """完全なデータ準備を実行"""
        logger.info("🚀 データ準備を開始...")
        
        success = True
        
        print("📋 実行ステップ:")
        print("1. Alpacaデータセットのダウンロード")
        print("2. サンプルデータセットの作成")
        print("3. データフォーマットの検証")
        print("4. データ統計の作成")
        print("-" * 50)
        
        # 1. Alpacaデータセットのダウンロード
        if not self.download_alpaca_dataset():
            success = False
        
        # 2. サンプルデータセットの作成
        if not self.create_sample_dataset():
            success = False
        
        # 3. データフォーマットの検証
        sample_files = list(self.samples_dir.glob("*.json"))
        for sample_file in sample_files:
            if not self.validate_data_format(str(sample_file)):
                success = False
        
        # 4. データ統計の作成
        if not self.create_data_statistics():
            success = False
        
        # 結果サマリー
        print("\n" + "="*50)
        if success:
            print("🎉 データ準備完了！")
            print(f"📁 生データ: {self.raw_dir}")
            print(f"📁 サンプルデータ: {self.samples_dir}")
            print(f"📁 統計データ: {self.processed_dir}")
        else:
            print("⚠️  データ準備中にエラーが発生しました")
        print("="*50)
        
        return success

def main():
    """メイン実行関数"""
    print("📊 TinySwallow LoRAチューニング - データ準備")
    print("="*60)
    
    preparer = DataPreparer()
    success = preparer.run_full_preparation()
    
    if not success:
        print("\n❌ データ準備に失敗しました。ログを確認してください。")
        exit(1)
    
    print("\n✅ データ準備が完了しました！")
    print("📝 次のステップ: Jupyter Notebookでトレーニングを開始してください")

if __name__ == "__main__":
    main()