#!/usr/bin/env python3
"""
sqlglotのJOIN情報アクセス方法を確認
"""

import sqlglot
import sqlglot.expressions as exp

def test_join_access():
    """JOIN情報へのアクセス方法を確認"""
    sql = """
    SELECT u.name, p.title
    FROM users u
    JOIN posts p ON u.id = p.user_id
    """
    
    print("=== JOIN Access Test ===")
    
    parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
    
    # joins プロパティからアクセス
    if hasattr(parsed, 'joins') and parsed.joins:
        print(f"Found {len(parsed.joins)} joins via joins property")
        
        for i, join in enumerate(parsed.joins):
            print(f"\nJOIN {i}:")
            print(f"  Type: {type(join)}")
            print(f"  Args: {join.args}")
            print(f"  This: {join.this}")
            
            # ON条件へのアクセス
            if 'on' in join.args:
                on_condition = join.args['on']
                print(f"  ON condition: {on_condition}")
                print(f"  ON type: {type(on_condition)}")
                
                # EQ条件の詳細
                if isinstance(on_condition, exp.EQ):
                    left = on_condition.left if hasattr(on_condition, 'left') else on_condition.this
                    right = on_condition.right if hasattr(on_condition, 'right') else on_condition.expression
                    
                    print(f"    Left: {left} (type: {type(left)})")
                    print(f"    Right: {right} (type: {type(right)})")
                    
                    # Column情報の取得
                    if isinstance(left, exp.Column):
                        left_table = left.table if hasattr(left, 'table') else None
                        left_col = left.name if hasattr(left, 'name') else left.this
                        print(f"    Left table: {left_table}, column: {left_col}")
                    
                    if isinstance(right, exp.Column):
                        right_table = right.table if hasattr(right, 'table') else None
                        right_col = right.name if hasattr(right, 'name') else right.this
                        print(f"    Right table: {right_table}, column: {right_col}")
            
            # USING句のテスト
            if 'using' in join.args:
                using_clause = join.args['using']
                print(f"  USING: {using_clause}")

def test_using_access():
    """USING句のアクセス方法を確認"""
    sql = """
    SELECT e.name, d.name
    FROM employees e
    JOIN departments d USING (dept_id)
    """
    
    print(f"\n=== USING Access Test ===")
    
    parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
    
    if hasattr(parsed, 'joins') and parsed.joins:
        for i, join in enumerate(parsed.joins):
            print(f"\nJOIN {i}:")
            print(f"  Args: {join.args}")
            
            if 'using' in join.args:
                using_clause = join.args['using']
                print(f"  USING clause: {using_clause}")
                print(f"  USING type: {type(using_clause)}")
                
                # USING句は通常リストになっている
                if isinstance(using_clause, list):
                    print(f"  USING columns:")
                    for col in using_clause:
                        print(f"    Column: {col} (type: {type(col)})")
                        if hasattr(col, 'name'):
                            print(f"      Name: {col.name}")

def test_from_where():
    """FROM + WHERE句のテスト"""
    sql = """
    SELECT c.name, o.total
    FROM customers c, orders o
    WHERE c.id = o.customer_id
    """
    
    print(f"\n=== FROM+WHERE Test ===")
    
    parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
    
    # FROM句の複数テーブル
    from_clause = parsed.find(exp.From)
    if from_clause:
        print(f"FROM: {from_clause}")
        print(f"FROM args: {from_clause.args}")
        
        # FROM句の'this'と'expressions'
        if 'this' in from_clause.args:
            print(f"FROM this: {from_clause.args['this']}")
        if 'expressions' in from_clause.args:
            print(f"FROM expressions: {from_clause.args['expressions']}")
        
        # FROM句でのカンマ区切りテーブルの場合
        # SQLGlotはこれを'this'に最初のテーブル、残りを'joins'に変換することがある
        print(f"Main FROM table: {from_clause.this}")
    
    # WHERE句の条件
    where_clause = parsed.find(exp.Where)
    if where_clause:
        print(f"\nWHERE: {where_clause}")
        
        equalities = list(where_clause.find_all(exp.EQ))
        for i, eq in enumerate(equalities):
            print(f"  EQ {i}: {eq}")
            left = eq.left if hasattr(eq, 'left') else eq.this
            right = eq.right if hasattr(eq, 'right') else eq.expression
            
            print(f"    Left: {left}")
            print(f"    Right: {right}")
            
            # テーブル情報の取得
            if isinstance(left, exp.Column) and hasattr(left, 'table'):
                print(f"    Left table: {left.table}, column: {left.name}")
            if isinstance(right, exp.Column) and hasattr(right, 'table'):
                print(f"    Right table: {right.table}, column: {right.name}")

if __name__ == "__main__":
    test_join_access()
    test_using_access() 
    test_from_where()