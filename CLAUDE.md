# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Development Workflow
```bash
# 1. ローカル開発（Cursor）
pip install -r requirements.txt
pip install -e .[dev]

# 2. コード作成・テスト後、GitHubにプッシュ
git add .
git commit -m "Implementation update"
git push origin main

# 3. Google Colabで実行
python scripts/setup_colab.py  # Colab環境セットアップ
python scripts/download_dependencies.py  # 依存関係インストール
python scripts/prepare_data.py  # データ準備
```

### Environment Setup
```bash
# Local development (Cursor + WSL2)
pip install -r requirements.txt
pip install -e .[dev]

# Google Colab environment
python scripts/setup_colab.py
pip install -r requirements_colab.txt

# Create project structure
python scripts/create_project_structure.py
```

### Available Console Commands
```bash
01tuning-train    # Training pipeline
01tuning-eval     # Evaluation/inference  
01tuning-data     # Data processing
```

### Development Tools
```bash
# Code formatting and linting
black src/ tests/ scripts/
flake8 src/ tests/ scripts/
mypy src/

# Testing
pytest tests/
```

## Architecture Overview

**01tuning** is a Japanese LLM fine-tuning project targeting TinySwallow models with dual environment support (local + Google Colab).

### Core Components (`src/`)
- **`config.py`**: Configuration management with hierarchical YAML configs and dataclasses
- **`model_utils.py`**: ModelManager using Unsloth for memory-efficient fine-tuning
- **`data_processing.py`**: DataProcessor for Alpaca format conversion
- **`training_utils.py`**: TrainingManager using TRL's SFTTrainer
- **`inference_utils.py`**: InferenceManager for model testing

### Configuration System (3-tier hierarchy)
- **`base_config.yaml`**: Project-wide defaults
- **`tinyswallow_config.yaml`**: TinySwallow-specific optimizations with Unsloth
- **`patent_config.yaml`**: Patent data specialization (4096 seq length, ROUGE/BLEU metrics)

### Key Technologies
- **Fine-tuning**: Unsloth (Colab optimization) + PEFT (LoRA) + TRL (SFTTrainer)
- **Target Model**: TinySwallow-7b-instruct-hf (Japanese language model)
- **Data**: Alpaca format + Japanese patent documents
- **Quantization**: 4-bit with bitsandbytes

### Known Issues in Current Code
Several typos exist in skeleton implementations that should be fixed:
- `src/config.py:79`: `trainig` → `training`
- `src/model_utils.py:50`: `mdoel` → `model`
- `src/model_utils.py:56`: `grandient` → `gradient`
- `src/data_processing.py:52`: `cofig` → `config`
- `src/training_utils.py`: Multiple `trainig` → `training` typos

---

# 01tuning プロジェクト進捗ドキュメント

## プロジェクト概要
- **プロジェクト名**: 01tuning
- **目的**: TinySwallowモデルと特許データを使用したLLMファインチューニング
- **開発環境**: WSL2 Linux, Cursor エディタ

## 現在の進捗状況 (2025-07-28)

### ✅ 完了したタスク

#### ステップ1: リポジトリセットアップ
- [x] リポジトリクローン完了
- [x] Cursorエディタでプロジェクト開いた

#### ステップ2: プロジェクト構造作成
- [x] プロジェクト構造作成スクリプト (`scripts/create_project_structure.py`) 作成
- [x] 必要なディレクトリ構造を自動作成
- [x] `__init__.py` ファイルを適切な場所に配置

#### ステップ3: 設定ファイル作成
- [x] `requirements.txt` (ローカル開発用依存関係)
- [x] `requirements_colab.txt` (Google Colab専用依存関係)
- [x] `.gitignore` (Git除外設定)
- [x] `configs/base_config.yaml` (基本設定)
- [x] `configs/tinyswallow_config.yaml` (TinySwallow専用設定)
- [x] `configs/patent_config.yaml` (特許データ専用設定)

#### ステップ4: 初期ファイル作成
- [x] `setup.py` (パッケージセットアップ)
- [x] `.gitkeep` ファイル (空ディレクトリ管理用)

#### コアモジュール作成 (完了)
- [x] `src/config.py` (設定管理モジュール)
- [x] `src/model_utils.py` (モデル関連ユーティリティ)
- [x] `src/data_processing.py` (データ前処理モジュール)
- [x] `src/training_utils.py` (トレーニングユーティリティ)
- [x] `src/inference_utils.py` (推論ユーティリティ)

### 🚧 進行中のタスク
- [x] スクリプトファイル作成（完了）
  - [x] `scripts/setup_colab.py` (Colab環境セットアップ)
  - [x] `scripts/download_dependencies.py` (完全実装済み - 環境検出、依存関係管理、検証機能付き)
  - [x] `scripts/prepare_data.py` (完全実装済み - Alpaca/特許データサンプル作成、統計機能付き)

### ✅ 最新完了タスク (2025-07-31更新)
- [x] **`notebooks/TinySwallow_1_5B_Alpaca_Tuning.ipynb`** - **完全実装済み**
  - Google Colab対応の完全動作ノートブック
  - TinySwallow-1.5Bモデルでのファインチューニング成功
  - 実行結果：100ステップ、Loss: 0.2915、GPU使用率10.6%
  - 推論テスト成功（フィボナッチ、首都、要約タスク）

### 📋 残りの未完了タスク
- [ ] テストファイル作成
  - [ ] `tests/test_model_utils.py`
  - [ ] `tests/test_data_processing.py`
- [ ] 残りのJupyter Notebook作成
  - [ ] `notebooks/TinySwallow_Patent_Tuning.ipynb`
  - [ ] `notebooks/evaluation.ipynb`

## 現在のディレクトリ構造

```
01tuning/
├── .gitignore
├── CLAUDE.md                              # このドキュメント
├── requirements.txt                       # ローカル開発用依存関係
├── requirements_colab.txt                 # Colab専用依存関係
├── setup.py                              # パッケージセットアップ
├── configs/                              # 設定ファイル
│   ├── base_config.yaml                  # 基本設定
│   ├── tinyswallow_config.yaml           # TinySwallow専用設定
│   └── patent_config.yaml                # 特許データ専用設定
├── src/                                  # Pythonソースコード
│   ├── __init__.py
│   ├── config.py                         # ✅ 設定管理 (スケルトン完成)
│   ├── model_utils.py                    # ✅ モデルユーティリティ (スケルトン完成)
│   ├── data_processing.py                # ✅ データ前処理 (スケルトン完成)
│   ├── training_utils.py                 # ✅ トレーニングユーティリティ (スケルトン完成)
│   └── inference_utils.py                # ✅ 推論ユーティリティ (スケルトン完成)
├── scripts/                              # 実行スクリプト
│   ├── create_project_structure.py       # ✅ プロジェクト構造作成
│   ├── setup_colab.py                    # ✅ Colab環境セットアップ
│   ├── download_dependencies.py          # ✅ 依存関係ダウンロード (完全実装)
│   └── prepare_data.py                   # ✅ データ準備 (完全実装)
├── data/                                 # データディレクトリ
│   ├── raw/ (.gitkeep)                   # 生データ
│   ├── processed/ (.gitkeep)             # 前処理済みデータ
│   └── samples/                          # サンプルデータ
├── notebooks/                            # Jupyter Notebook
│   ├── TinySwallow_1_5B_Alpaca_Tuning.ipynb  # ✅ 完全実装済み (動作確認済み)
│   ├── TinySwallow_Patent_Tuning.ipynb       # ❌ 未作成
│   ├── evaluation.ipynb                      # ❌ 未作成
│   └── sample.md                             # ✅ サンプルファイル
├── tests/                                # テストコード
│   ├── __init__.py
│   ├── test_model_utils.py               # ❌ 未作成
│   └── test_data_processing.py           # ❌ 未作成
├── docs/                                 # ドキュメント
│   ├── git-github-workflow-guide.md         # ✅ Git/GitHubワークフローガイド
│   ├── git-quick-reference.md               # ✅ Git クイックリファレンス
│   └── git-visual-guide.md                  # ✅ Git ビジュアルガイド
├── models/                               # モデル関連
│   └── saved_models/ (.gitkeep)          # 保存モデル
└── logs/ (.gitkeep)                      # ログファイル
```

## 次のステップ

### 優先度高（完了済み）
1. ✅ スクリプトファイル作成（完了）
   - 全4つのスクリプトファイルが完全実装済み

2. ✅ **メインノートブック作成（完了）**
   - `notebooks/TinySwallow_1_5B_Alpaca_Tuning.ipynb` **完全実装済み**

### 優先度中  
3. 残りのJupyter Notebook作成
   - `notebooks/TinySwallow_Patent_Tuning.ipynb` 
   - `notebooks/evaluation.ipynb`

### 優先度低
4. テストファイル作成
   - `tests/test_model_utils.py`
   - `tests/test_data_processing.py`

## 最新の実装状況 (2025-07-31更新)

### 完全実装済みスクリプト
- **`download_dependencies.py`** (293行): 
  - 環境自動検出（Colab/ローカル）
  - CUDA利用可能性チェック
  - 依存関係の段階的インストール
  - インストール検証機能
  - 詳細なエラーハンドリング

- **`prepare_data.py`** (352行):
  - Alpacaデータセットダウンロード
  - 日本語サンプルデータ作成（Alpaca/特許/カスタム）
  - データフォーマット検証
  - データ統計生成機能

### 完全実装済みJupyter Notebook
- **`TinySwallow_1_5B_Alpaca_Tuning.ipynb`** - **動作確認済み**
  - Google Colab T4 GPU対応
  - TinySwallow-1.5B-InstructモデルでLoRAファインチューニング
  - 実行成功：100ステップ、Loss: 0.2915、GPU使用率10.6%
  - 推論テスト成功（フィボナッチ、首都、要約タスク）
  - モデル保存機能（LoRA、16bit/4bit マージ、GGUF対応）

### 新規追加ドキュメント
- **`docs/git-github-workflow-guide.md`** - Git/GitHubワークフローガイド
- **`docs/git-quick-reference.md`** - Gitクイックリファレンス  
- **`docs/git-visual-guide.md`** - Gitビジュアルガイド

## 設定ファイルの特徴

### base_config.yaml
- プロジェクト全体の基本設定
- データ、モデル、トレーニング、LoRA、ログ、評価の設定を含む

### tinyswallow_config.yaml
- TinySwallowモデル専用の最適化設定
- Unsloth、量子化設定を含む
- Alpacaデータセット用のテンプレート設定

### patent_config.yaml
- 特許データ専用設定
- 長い系列長 (4096) に対応
- 特許文書の前処理とクリーニング設定
- ROUGE/BLEU評価メトリクス設定

## 技術スタック

### 開発フロー
```
ローカル開発（Cursor） → GitHub → Google Colab
```

### 環境構成
- **ローカル開発**: Cursor エディタ + WSL2 Linux
- **バージョン管理**: GitHub
- **実行環境**: Google Colab（GPU利用）

### 技術要素
- **言語**: Python 3.8+
- **主要ライブラリ**: 
  - PyTorch 2.0+
  - Transformers 4.42.1+
  - Datasets 2.14.0+
  - Unsloth (Colab GPU最適化)
  - PEFT (LoRA)
  - TRL (SFTTrainer)
- **開発ツール**: pytest, black, flake8, mypy, Git
- **実行環境**: Google Colab（T4/V100 GPU）

## 注意事項

### 開発フロー関連
- **ローカル開発**: Cursor + WSL2環境で開発・テスト
- **GitHub**: バージョン管理とColab間のコード同期
- **Google Colab**: GPU利用による実際のファインチューニング実行

### 実装状況
- コアモジュール（`src/`）: 基本的なスケルトン構造のみ実装済み
- スクリプトファイル（`scripts/`）: 完全実装済み
- 設定ファイル（`configs/`）: 本格運用向けに調整済み

### 既知の修正すべきtypo
- `prepare_data.py:38`: `yaml.sage_load` → `yaml.safe_load`
- `prepare_data.py:75`: `logger.errro` → `logger.error`
- `prepare_data.py:98`: メソッド名の不整合
- `prepare_data.py:221`: `'instuction'` → `'instruction'`

---

# ✅ 最新完了タスク (2025-08-01更新)

## 🎯 特許データ処理の問題解決（完了）

### 問題の発見と解決
1. **初期問題**: 200個の特許データから2個のChatMLペアしか生成されない問題
2. **根本原因**: logger未定義エラーにより処理が中断
3. **解決策**: `src/patent_processing/text_processor.py`にlogger import追加

### データ抽出改善実装
- **BestMode/InventionMode対応**: 段階的に抽出ソースを拡張
- **段落番号保持機能**: 【XXXX】形式の段落番号を保持する`_extract_text_with_paragraph_numbers()`メソッド実装
- **抽出カバレッジ向上**: 97.0% → 98.5%に改善

### 生成されたデータセット
- **完全データセット**: 420個のChatMLペア (46MB)
- **段落番号付きデータセット**: `chatml_training_with_paragraphs_full.json`

## 🎯 インタラクティブ学習データセット生成（完了）

### Option 1: 段落単位データセット
```bash
python3 generate_option1_dataset.py
```

**特徴**:
- **3,655個の学習サンプル** (79.8MB)
- 各段落が独立したChatMLペア
- 前段落の文脈情報を含む
- 「【XXXX】の段落を生成してください」の明示的指示

**フォーマット例**:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "あなたは特許文書の専門家です。与えられた特許請求の範囲と文脈に基づいて、指定された段落番号の実施形態を生成してください。"
    },
    {
      "role": "user", 
      "content": "特許番号: 7620367\n\n前の段落:\n【0009】\n...\n\n【請求項】\n...\n\n上記に基づいて【0010】の段落を生成してください。"
    },
    {
      "role": "assistant",
      "content": "【0010】\n以下に添付図面を参照しながら、本開示の好適な実施の形態について詳細に説明する。..."
    }
  ]
}
```

### Option 2: 会話履歴形式データセット
```bash
python3 generate_option2_dataset.py
```

**特徴**:
- **49会話、7,357ターン** (3.2MB)
- 「次の段落をお願いします」コマンド対応
- 多ターン会話形式で自然な対話フロー
- 平均74.6段落/特許、最大369段落

**フォーマット例**:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "あなたは特許文書の専門家です。ユーザーの請求項に基づいて、実施形態を段落ごとに対話形式で生成してください。ユーザーが「次へ」と言ったら次の段落を生成してください。"
    },
    {
      "role": "user",
      "content": "以下の特許請求の範囲に基づいて、実施形態を段落ごとに生成してください：\n\n【請求項1】\n...\n\n最初の段落からお願いします。"
    },
    {
      "role": "assistant", 
      "content": "【0009】\n本開示の実施形態の内容を列記して説明する。..."
    },
    {
      "role": "user",
      "content": "次の段落をお願いします。"
    },
    {
      "role": "assistant",
      "content": "【0010】\n以下に添付図面を参照しながら、本開示の好適な実施の形態について詳細に説明する。..."
    }
  ]
}
```

## 🎯 データセット比較分析（完了）

### 比較サマリー

| 項目 | Option 1: 段落単位 | Option 2: 会話履歴 |
|------|-------------|-------------|
| **データ構造** | 個別ChatMLペア | 多ターン会話 |
| **総レコード数** | 3,655件 | 49会話 |
| **ファイルサイズ** | 79.8MB | 3.2MB |
| **学習ターン数** | 3,655ターン | 7,357ターン |
| **段落指定生成** | ◯ 明示的指定 | △ 順次のみ |
| **対話継続性** | △ 文脈制限あり | ◯ 完全履歴 |
| **「次へ」理解** | × 未対応 | ◯ 完全対応 |

### 推奨学習アプローチ
1. **フェーズ1**: Option 2で対話パターン習得
2. **フェーズ2**: Option 1で段落生成精度向上

詳細分析: `/mnt/d/20250728/01tuning/dataset_comparison_analysis.md`

## 📁 更新されたファイル構成

### 特許処理モジュール
```
src/patent_processing/
├── __init__.py
└── text_processor.py                  # ✅ logger修正、段落番号保持機能追加
```

### 生成されたデータセット
```
data/processed/
├── chatml_training_with_paragraphs_full.json    # 420個の基本データセット
├── option1_paragraph_unit.json                  # 3,655個の段落単位データセット  
└── option2_conversation.json                    # 49会話の対話形式データセット
```

### データセット生成スクリプト
```
├── generate_option1_dataset.py        # ✅ 段落単位データセット生成
├── generate_option2_dataset.py        # ✅ 会話履歴データセット生成
└── generate_updated_dataset.py        # ✅ 段落番号付きデータセット生成
```

### 分析ドキュメント
```
├── dataset_comparison_analysis.md     # ✅ データセット比較分析レポート
└── 修正内容整理.md                   # ユーザー提供の問題解決記録
```

## 🔧 実装された主要機能

### 1. 段落番号保持機能
```python
def _extract_text_with_paragraph_numbers(self, element) -> str:
    """段落番号【XXXX】を含めてテキストを抽出"""
    # XML属性から段落番号を取得し【XXXX】形式で保持
```

### 2. 段階的データ抽出
- **Stage 1**: EmbodimentDescription
- **Stage 2**: BestMode (救済率 +0.5%)  
- **Stage 3**: InventionMode (救済率 +1.5%)

### 3. 2つの学習データセット形式
- **Option 1**: 明示的段落指定による独立学習
- **Option 2**: 対話継続による自然なフロー学習

## 🎯 達成された目標

1. ✅ **データ抽出問題の完全解決**: 2個 → 420個のChatMLペア生成
2. ✅ **段落番号保持**: 【XXXX】形式の完全保持
3. ✅ **インタラクティブ学習準備**: 2つの異なるアプローチでデータセット生成
4. ✅ **トライアンドエラー環境**: 両方式での実験準備完了

## 🚀 次のステップ

### 学習実行フェーズ
1. **Option 2での基礎学習**: 対話パターンと「次へ」コマンド理解
2. **Option 1での精度向上**: 大量データによる段落生成品質向上
3. **性能比較評価**: 両アプローチの効果測定
4. **ハイブリッドモデル検討**: 最適な組み合わせの探索

### 実用化フェーズ  
1. **Google Colabでの学習実行**: TinySwallow-1.5Bモデルでの実験
2. **推論テスト**: 実際の特許請求項での段落生成テスト
3. **ユーザーインターフェース**: 対話形式での段階的生成システム構築