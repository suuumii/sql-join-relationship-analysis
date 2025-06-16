# SQL JOIN Relationship Analysis Tool

PythonでSQLクエリのJOIN関係を解析し、テーブル間の親子関係を特定するツールです。

## 機能

- **sqlglot**を使用したSQL解析（MySQL方言対応）
- 複雑なJOIN構文の解析：
  - サブクエリ内のJOIN
  - USING句
  - NATURAL JOIN
  - 複数テーブルのFROM句 + WHERE句での結合条件
- 外部キー命名規則（`*_id`）から親子関係を自動推測
- CSV形式での結果出力
- NetworkXによるテーブル関係図の生成

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な使用方法

```python
from sql_join_analyzer import SQLJoinAnalyzer

analyzer = SQLJoinAnalyzer()

# SQL クエリを解析
sql = """
SELECT u.name, p.title
FROM users u
JOIN posts p ON u.id = p.user_id
"""

relationships = analyzer.analyze_sql(sql)

# CSV出力
analyzer.export_to_csv('relationships.csv')

# グラフ可視化
analyzer.generate_graph_visualization('graph.png')
```

### 複数クエリの一括解析

```python
queries = [
    "SELECT * FROM users u JOIN posts p ON u.id = p.user_id",
    "SELECT * FROM orders o, customers c WHERE o.customer_id = c.id"
]

all_relationships = analyzer.analyze_multiple_queries(queries)
```

## 対応するSQL構文

### 1. 標準的なJOIN
```sql
SELECT u.name, p.title
FROM users u
INNER JOIN posts p ON u.id = p.user_id
LEFT JOIN categories c ON p.category_id = c.id
```

### 2. USING句
```sql
SELECT e.name, d.name
FROM employees e
JOIN departments d USING (department_id)
```

### 3. NATURAL JOIN
```sql
SELECT *
FROM employees
NATURAL JOIN departments
```

### 4. FROM句での複数テーブル + WHERE条件
```sql
SELECT o.id, c.name, p.name
FROM orders o, customers c, products p
WHERE o.customer_id = c.id AND o.product_id = p.id
```

### 5. サブクエリ内のJOIN
```sql
SELECT u.name, stats.post_count
FROM users u
LEFT JOIN (
    SELECT user_id, COUNT(*) as post_count
    FROM posts p
    JOIN categories c ON p.category_id = c.id
    GROUP BY user_id
) stats ON u.id = stats.user_id
```

## 出力形式

### CSV出力
```csv
table1,column1,column_definition1,table2,column2,column_definition2
users,id,INT PRIMARY KEY,posts,user_id,INT FOREIGN KEY
posts,category_id,INT FOREIGN KEY,categories,id,INT PRIMARY KEY
```

### 関係情報の推測ルール

1. **外部キー推測**: `*_id` パターンから親子関係を推測
2. **カラム型推測**: 
   - `id` → `INT PRIMARY KEY`
   - `*_id` → `INT FOREIGN KEY`
   - `*_at`, `*_time` → `DATETIME`
   - `*_date` → `DATE`
   - `*_count`, `*_num` → `INT`
   - `*_flag`, `is_*` → `BOOLEAN`
   - その他 → `VARCHAR(255)`

## 実行例

```bash
# サンプル実行（推奨）
python examples/example_usage.py

# 基本テスト
python tests/simple_test.py

# 包括テスト
python tests/final_test.py

# 個別使用
python -c "
from sql_join_analyzer import SQLJoinAnalyzer
analyzer = SQLJoinAnalyzer()
relationships = analyzer.analyze_sql('SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id')
print(f'Found {len(relationships)} relationships')
"
```

## ファイル構成

```
sql-join-relationship-analysis/
├── sql_join_analyzer.py      # メインのアナライザークラス
├── requirements.txt          # 依存関係
├── README.md                 # このファイル
├── examples/                 # 使用例
│   ├── __init__.py
│   └── example_usage.py      # 使用例とサンプルケース
├── tests/                    # テストファイル
│   ├── __init__.py
│   ├── test_queries.py       # サンプルクエリ集
│   ├── final_test.py         # 包括テスト
│   ├── simple_test.py        # 基本テスト
│   ├── test_visualization.py # 可視化テスト
│   └── debug_*.py            # デバッグファイル
└── output/                   # 出力ファイル
    ├── .gitkeep
    └── (生成されたCSVやPNGファイル)
```

## 制限事項

- スキーマ情報が不明な場合、カラム型は命名規則から推測
- NATURAL JOINは具体的なカラム名を特定できない場合がある
- 複雑なサブクエリや動的SQLには対応していない場合がある