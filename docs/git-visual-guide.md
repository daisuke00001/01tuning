# Git & GitHub 視覚的図解ガイド 📊

このドキュメントは、Git/GitHubの操作を視覚的に理解するための図解集です。

## 📋 目次
1. [基本的なGitの流れ](#基本的なgitの流れ)
2. [ブランチ戦略](#ブランチ戦略)
3. [Pull Requestワークフロー](#pull-requestワークフロー)
4. [コンフリクト解決](#コンフリクト解決)
5. [チーム開発フロー](#チーム開発フロー)

---

## 基本的なGitの流れ

### 📁 Git の三つのエリア

```mermaid
flowchart TD
    A["📁 ワーキングディレクトリ<br/>作業中のファイル<br/>- 編集<br/>- 追加<br/>- 削除"] 
    B["📦 ステージングエリア<br/>コミット予定のファイル<br/>- git add で追加<br/>- git reset で取消"]
    C["💾 ローカルリポジトリ<br/>コミット済みファイル<br/>- git commit で保存<br/>- 履歴として管理"]
    D["☁️ リモートリポジトリ<br/>共有リポジトリ<br/>- git push で送信<br/>- git pull で取得"]
    
    A -->|git add| B
    B -->|git commit| C
    C -->|git push| D
    D -->|git pull| A
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#c8e6c9
    style D fill:#f3e5f5
```

### ⚡ 日常の作業サイクル

```mermaid
flowchart TD
    Start["🌅 作業開始"] --> Status["git status<br/>📊 現状確認"]
    Status --> Pull["git pull<br/>⬇️ 最新取得"]
    Pull --> Edit["🖊️ ファイル編集"]
    Edit --> Add["git add .<br/>📦 変更をステージング"]
    Add --> Commit["git commit -m 'message'<br/>💾 変更をコミット"]
    Commit --> Push["git push<br/>☁️ リモートに送信"]
    Push --> End["🌙 作業終了"]
    
    Edit --> Status
    
    style Start fill:#c8e6c9
    style End fill:#f3e5f5
```

---

## ブランチ戦略

### 🌿 Feature Branch ワークフロー

```mermaid
gitGraph
    commit id: "初期設定"
    commit id: "基本機能"
    
    branch feature/user-auth
    checkout feature/user-auth
    commit id: "ログイン画面"
    commit id: "認証ロジック"
    commit id: "テスト追加"
    
    checkout main
    commit id: "ドキュメント更新"
    
    merge feature/user-auth
    commit id: "ユーザー認証完成"
    
    branch feature/dashboard
    checkout feature/dashboard
    commit id: "ダッシュボード画面"
    commit id: "データ表示"
    
    checkout main
    branch hotfix/login-bug
    checkout hotfix/login-bug
    commit id: "ログインバグ修正"
    
    checkout main
    merge hotfix/login-bug
    commit id: "緊急修正リリース"
    
    merge feature/dashboard
    commit id: "v1.1 リリース"
```

### 🔄 ブランチの種類と用途

```mermaid
flowchart TD
    Main["🏠 main ブランチ<br/>本番コード<br/>常に安定した状態"]
    
    Feature["🌿 feature/ ブランチ<br/>新機能開発<br/>feature/user-login<br/>feature/payment"]
    
    Bugfix["🐛 bugfix/ ブランチ<br/>バグ修正<br/>bugfix/login-error<br/>bugfix/payment-issue"]
    
    Hotfix["🚨 hotfix/ ブランチ<br/>緊急修正<br/>hotfix/security-patch<br/>hotfix/critical-bug"]
    
    Release["🚀 release/ ブランチ<br/>リリース準備<br/>release/v1.0.0<br/>release/v2.0.0"]
    
    Main --> Feature
    Main --> Bugfix
    Main --> Hotfix
    Main --> Release
    
    Feature --> Main
    Bugfix --> Main
    Hotfix --> Main
    Release --> Main
    
    style Main fill:#c8e6c9
    style Feature fill:#e1f5fe
    style Bugfix fill:#fff3e0
    style Hotfix fill:#ffebee
    style Release fill:#f3e5f5
```

---

## Pull Requestワークフロー

### 🔄 PR作成から マージまで

```mermaid
flowchart TD
    A["🌿 機能ブランチで開発"] --> B["git push origin feature/xxx<br/>☁️ ブランチをプッシュ"]
    B --> C["🔄 GitHub で Pull Request 作成"]
    C --> D["📝 PR説明を記入<br/>- 変更内容<br/>- テスト内容<br/>- 関連Issue"]
    D --> E["👀 コードレビュー依頼"]
    E --> F{"✅ レビュー結果"}
    
    F -->|承認| G["🎯 main ブランチにマージ"]
    F -->|修正要求| H["🔧 指摘事項を修正"]
    
    H --> I["git add & commit<br/>📝 修正をコミット"]
    I --> J["git push<br/>☁️ 修正をプッシュ"]
    J --> E
    
    G --> K["🗑️ 機能ブランチ削除"]
    K --> L["git checkout main<br/>🏠 メインブランチに戻る"]
    L --> M["git pull origin main<br/>⬇️ 最新を取得"]
    
    style C fill:#fff3e0
    style G fill:#c8e6c9
    style H fill:#ffebee
```

### 📊 レビューのポイント

```mermaid
mindmap
    root((コードレビュー))
        機能性
            要件を満たしているか
            エッジケースの考慮
            エラーハンドリング
        品質
            コードの可読性
            命名規則の遵守
            コメントの適切性
        安全性
            セキュリティの確認
            権限の適切な管理
            入力値の検証
        性能
            処理速度
            メモリ使用量
            スケーラビリティ
        テスト
            テストケースの網羅性
            テストの実行可能性
            モックの適切な使用
```

---

## コンフリクト解決

### ⚔️ マージコンフリクトの発生パターン

```mermaid
gitGraph
    commit id: "共通のベース"
    
    branch feature-a
    checkout feature-a
    commit id: "A: ファイル変更"
    
    checkout main
    branch feature-b
    checkout feature-b
    commit id: "B: 同じファイル変更"
    
    checkout main
    merge feature-a
    commit id: "A をマージ"
    
    merge feature-b
    commit id: "コンフリクト発生!"
```

### 🔧 コンフリクト解決の手順

```mermaid
flowchart TD
    A["⚔️ コンフリクト発生"] --> B["git status<br/>📊 コンフリクトファイル確認"]
    B --> C["🔍 コンフリクトマーカーを確認<br/><<<<<<< HEAD<br/>=======<br/>>>>>>>> branch"]
    C --> D["✏️ ファイルを手動編集<br/>コンフリクトを解決"]
    D --> E["🧪 動作テスト<br/>解決内容を確認"]
    E --> F["git add ファイル名<br/>📦 解決をステージング"]
    F --> G["git commit<br/>💾 マージコミット作成"]
    G --> H["✅ コンフリクト解決完了"]
    
    style A fill:#ffebee
    style D fill:#fff3e0
    style H fill:#c8e6c9
```

---

## チーム開発フロー

### 👥 複数人での開発フロー

```mermaid
flowchart TD
    subgraph "開発者A"
        A1["🌿 feature/login ブランチ"] --> A2["💻 ログイン機能開発"]
        A2 --> A3["🔄 PR作成"]
    end
    
    subgraph "開発者B"
        B1["🌿 feature/dashboard ブランチ"] --> B2["💻 ダッシュボード開発"]
        B2 --> B3["🔄 PR作成"]
    end
    
    subgraph "レビュアー"
        R1["👀 コードレビュー"] --> R2["✅ マージ承認"]
    end
    
    subgraph "main ブランチ"
        M1["🏠 安定版コード"] --> M2["🎯 機能統合"]
        M2 --> M3["🚀 リリース"]
    end
    
    A3 --> R1
    B3 --> R1
    R2 --> M2
    
    style M1 fill:#c8e6c9
    style M3 fill:#f3e5f5
```

### 🔄 継続的インテグレーション (CI/CD)

```mermaid
flowchart LR
    A["💻 コード変更"] --> B["git push<br/>☁️ プッシュ"]
    B --> C["🤖 CI実行<br/>自動テスト"]
    C --> D{"✅ テスト結果"}
    D -->|成功| E["🔄 PR作成可能"]
    D -->|失敗| F["❌ 修正が必要"]
    F --> A
    E --> G["👀 レビュー"]
    G --> H["🎯 マージ"]
    H --> I["🚀 自動デプロイ"]
    
    style C fill:#e1f5fe
    style E fill:#c8e6c9
    style F fill:#ffebee
    style I fill:#f3e5f5
```

---

## 💡 図解の活用方法

### 📖 学習順序
1. **基本的なGitの流れ** を理解
2. **ブランチ戦略** でチーム開発を学習
3. **Pull Request** で協業方法を習得
4. **コンフリクト解決** でトラブル対応を練習
5. **チーム開発フロー** で実践的な開発を体験

### 🎯 実践のコツ
- 図解を見ながら実際にコマンドを実行
- 各段階でのファイル状態を確認
- エラーが発生したら図解で現在位置を把握
- チームメンバーと図解を共有して認識合わせ

### 📱 参考リンク
- [Git公式ドキュメント](https://git-scm.com/book/ja/v2)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Mermaid公式サイト](https://mermaid-js.github.io/mermaid/)

---

*この図解ガイドと合わせて、[Git学習ガイド](./git-github-workflow-guide.md) と [クイックリファレンス](./git-quick-reference.md) もご活用ください！*