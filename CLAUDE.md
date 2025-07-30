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

### 📋 未完了のタスク
- [ ] テストファイル作成
  - [ ] `tests/test_model_utils.py`
  - [ ] `tests/test_data_processing.py`
- [ ] Jupyter Notebook作成
  - [ ] `notebooks/TinySwallow_1_5B_Alpaca_Tuning.ipynb`
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
│   ├── TinySwallow_1_5B_Alpaca_Tuning.ipynb  # ❌ 未作成
│   ├── TinySwallow_Patent_Tuning.ipynb       # ❌ 未作成
│   └── evaluation.ipynb                      # ❌ 未作成
├── tests/                                # テストコード
│   ├── __init__.py
│   ├── test_model_utils.py               # ❌ 未作成
│   └── test_data_processing.py           # ❌ 未作成
├── docs/                                 # ドキュメント (空)
├── models/                               # モデル関連
│   └── saved_models/ (.gitkeep)          # 保存モデル
└── logs/ (.gitkeep)                      # ログファイル
```

## 次のステップ

### 優先度高
1. ✅ スクリプトファイル作成（完了）
   - 全4つのスクリプトファイルが完全実装済み

### 優先度中  
2. Jupyter Notebook作成
   - `notebooks/TinySwallow_1_5B_Alpaca_Tuning.ipynb`
   - `notebooks/TinySwallow_Patent_Tuning.ipynb` 
   - `notebooks/evaluation.ipynb`

### 優先度低
3. テストファイル作成
   - `tests/test_model_utils.py`
   - `tests/test_data_processing.py`
4. ドキュメント作成

## 最新の実装状況 (2025-07-29更新)

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