# SQL Folder Analysis Tool

**フォルダ内のSQLファイルを一括解析**し、テーブル間のJOIN関係を特定するツールです。

## 主な機能

- **フォルダ一括解析**: 指定フォルダ内の全`.sql`ファイルを自動解析
- **再帰的解析**: サブフォルダも含めて全SQLファイルを処理
- **関係統合**: 複数ファイルから重複を排除した関係を抽出
- **多様なJOIN対応**: INNER, LEFT, RIGHT JOIN、USING、NATURAL、カンマ結合
- **複雑クエリ対応**: サブクエリ、ウィンドウ関数、集計処理
- **外部キー推測**: `*_id`命名規則から親子関係を自動推測
- **多形式出力**: CSV、グラフ画像、サマリーテキスト

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

### フォルダ内SQLファイルの一括解析

```python
from folder_analyzer import FolderSQLAnalyzer

folder_analyzer = FolderSQLAnalyzer()

# 単一フォルダ解析
results = folder_analyzer.analyze_folder("sql_queries_folder")

# サブフォルダを含む再帰的解析
results = folder_analyzer.analyze_with_subdirectories("root_folder")

# 結果をエクスポート
folder_analyzer.export_results(prefix="my_analysis")
```

## 出力形式

### CSV出力
```csv
table1,column1,column_definition1,table2,column2,column_definition2
users,id,INT PRIMARY KEY,posts,user_id,INT FOREIGN KEY
posts,category_id,INT FOREIGN KEY,categories,id,INT PRIMARY KEY
```

### PNG画像出力
- NetworkXによるテーブル関係図
- ノード: テーブル名
- エッジ: JOIN関係（矢印付き）

### TXT概要出力
- 解析したファイル一覧
- 発見された関係の詳細リスト
- 統計情報（ファイル数、関係数、テーブル数）

## 実行例

```bash
# フォルダ解析デモ（推奨）
python examples/folder_demo.py

# フォルダ解析（コマンドライン）
python folder_analyzer.py

# サンプルSQLファイルで解析テスト
python -c "
from folder_analyzer import FolderSQLAnalyzer
analyzer = FolderSQLAnalyzer()
analyzer.analyze_folder('input_sample')
analyzer.export_results(prefix='sample_test')
"
```

## ファイル構成

```
sql-join-relationship-analysis/
├── sql_join_analyzer.py      # ベースアナライザークラス
├── folder_analyzer.py        # フォルダ一括解析ツール（メイン）
├── requirements.txt          # 依存関係
├── README.md                 # このファイル
├── .gitignore               # Git除外設定
├── examples/                 # 使用例
│   ├── __init__.py
│   └── folder_demo.py        # フォルダ解析デモ
├── input_sample/             # サンプルSQLファイル
│   ├── README.md             # サンプルファイル説明
│   ├── user_management.sql   # ユーザー管理
│   ├── order_processing.sql  # 注文処理
│   ├── employee_hierarchy.sql # 従業員階層
│   ├── inventory_management.sql # 在庫管理
│   ├── sales_analytics.sql   # 売上分析
│   ├── blog_content.sql      # ブログコンテンツ
│   ├── financial_transactions.sql # 金融取引
│   ├── legacy_comma_joins.sql # レガシー結合
│   └── complex_subqueries.sql # 複雑なサブクエリ
└── output/                   # 出力ファイル
    ├── .gitkeep
    └── (生成されたCSVやPNGファイル)
```

## 特徴

- **大量ファイル対応**: 数百〜数千のSQLファイルも効率的に処理
- **重複関係排除**: 複数ファイル間の同一関係を自動で統合
- **多様なSQL構文**: レガシーなカンマ結合から最新のウィンドウ関数まで対応
- **視覚的出力**: テーブル関係図で複雑な依存関係を一目で把握
- **詳細レポート**: ファイル別解析 + 全体統計の2段階レポート