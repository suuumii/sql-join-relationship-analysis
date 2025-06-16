# Input Sample SQLファイル

このフォルダには、SQL JOIN関係解析ツールのテスト用SQLファイルが含まれています。

## ファイル一覧

### 1. `user_management.sql`
- **用途**: ユーザー管理関連
- **特徴**: LEFT JOIN, INNER JOIN の組み合わせ
- **関連テーブル**: users, profiles, user_roles, roles

### 2. `order_processing.sql`
- **用途**: 注文処理関連
- **特徴**: 複数のINNER JOIN, LEFT JOIN
- **関連テーブル**: orders, customers, order_items, products, categories, suppliers

### 3. `employee_hierarchy.sql`
- **用途**: 従業員階層管理
- **特徴**: USING句、自己結合
- **関連テーブル**: employees, departments, positions, locations

### 4. `inventory_management.sql`
- **用途**: 在庫管理
- **特徴**: 複数のLEFT JOIN, INNER JOIN
- **関連テーブル**: products, inventory, warehouses, suppliers, categories

### 5. `sales_analytics.sql`
- **用途**: 売上分析
- **特徴**: 集計関数、GROUP BY、HAVING
- **関連テーブル**: customers, orders, order_items, regions, customer_segments

### 6. `blog_content.sql`
- **用途**: ブログコンテンツ管理
- **特徴**: 多対多関係、集計関数
- **関連テーブル**: posts, users, categories, comments, ratings, post_tags, tags

### 7. `financial_transactions.sql`
- **用途**: 金融取引管理
- **特徴**: 日付条件、複数のJOIN
- **関連テーブル**: transactions, accounts, customers, branches, employees

### 8. `legacy_comma_joins.sql`
- **用途**: レガシーなカンマ結合
- **特徴**: FROM句でのカンマ区切り、WHERE句での結合条件
- **関連テーブル**: orders, customers, order_items, products, suppliers, warehouses, inventory

### 9. `complex_subqueries.sql`
- **用途**: 複雑なサブクエリ
- **特徴**: ネストしたサブクエリ、ウィンドウ関数
- **関連テーブル**: customers, orders, order_items, products, categories, customer_loyalty, loyalty_levels

## 使用方法

```bash
# このフォルダを解析
python3 folder_analyzer.py

# または
python3 -c "
from folder_analyzer import FolderSQLAnalyzer
analyzer = FolderSQLAnalyzer()
results = analyzer.analyze_folder('input_sample')
analyzer.export_results(prefix='input_sample_analysis')
"
```

## 期待される解析結果

- **総ファイル数**: 9ファイル
- **推定関係数**: 40-50関係
- **関連テーブル数**: 25-30テーブル

これらのファイルは、実際のアプリケーションでよく見られるSQLパターンを網羅しており、JOIN関係解析ツールの動作確認に最適です。