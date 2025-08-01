# Extract Claims and Implementations メソッド詳細ロジック

## 1. データ構造の理解

### 入力データ形式
```json
[
  {"patent_id": "7620367", "section": "abstract", "text": "..."},
  {"patent_id": "7620367", "section": "claims", "text": "..."},
  {"patent_id": "7620367", "section": "detailed_description", "text": "..."},
  {"patent_id": "8901234", "section": "abstract", "text": "..."}
]
```

## 2. グループ化処理

### patent_idごとのグループ化
```python
patents_by_id = {
  "7620367": {
    "abstract": "課題文...",
    "claims": "請求項1...", 
    "detailed_description": "実施形態では..."
  },
  "8901234": {
    "abstract": "別の課題文...",
    "background_art": "従来技術では..."
  }
}
```

## 3. セクション検索の優先順位

### 請求項セクション（user側）
1. `claims` ← 最優先（正式な請求項）
2. `claim` ← 単数形の場合
3. `abstract` ← 要約を代用

### 実施形態セクション（assistant側）  
1. `detailed_description` ← 最優先（詳細説明）
2. `description` ← 一般的説明
3. `embodiment` ← 実施形態
4. `background_art` ← 背景技術

## 4. ペア作成の判定フロー

```python
for patent_id, sections in patents_by_id.items():
    # ステップ1: 請求項検索
    claims_text = None
    for section_name in ['claims', 'claim', 'abstract']:
        if section_name in sections and sections[section_name].strip():
            claims_text = sections[section_name]
            break
    
    # ステップ2: 実施形態検索  
    implementation_text = None
    for section_name in ['detailed_description', 'description', 'embodiment', 'background_art']:
        if section_name in sections and sections[section_name].strip():
            implementation_text = sections[section_name]
            break
    
    # ステップ3: ペア作成判定
    if claims_text and implementation_text:
        # 前処理 + 文字数チェック後にペア作成
        pair = create_pair(claims_text, implementation_text)
```

## 5. 統計情報の追加

改善版では以下の統計を出力：
- `success`: 成功したペア数
- `no_claims`: 請求項セクションが見つからない数
- `no_implementation`: 実施形態セクションが見つからない数  
- `too_short`: 文字数不足でスキップされた数

これにより、データの活用率が明確になります。