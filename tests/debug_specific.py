#!/usr/bin/env python3
"""
特定の問題をデバッグ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlglot
import sqlglot.expressions as exp
from sql_join_analyzer import SQLJoinAnalyzer

def debug_from_where():
    """FROM-WHERE句の問題をデバッグ"""
    sql = """
    SELECT c.name, o.total
    FROM customers c, orders o
    WHERE c.id = o.customer_id
    """
    
    print("=== FROM-WHERE Debug ===")
    print(f"SQL: {sql.strip()}")
    
    parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
    
    print(f"\nParsed args keys: {list(parsed.args.keys())}")
    
    # joins情報
    if 'joins' in parsed.args:
        joins = parsed.args['joins']
        print(f"Joins: {joins}")
        print(f"Number of joins: {len(joins)}")
        
        for i, join in enumerate(joins):
            print(f"\nJoin {i}:")
            print(f"  Object: {join}")
            print(f"  Args: {join.args}")
            print(f"  Has 'on' in args: {'on' in join.args}")
            
    # WHERE句
    if 'where' in parsed.args:
        where = parsed.args['where']
        print(f"\nWHERE clause: {where}")
        print(f"WHERE args: {where.args}")
        
        # EQ条件
        eq_conditions = list(where.find_all(exp.EQ))
        print(f"EQ conditions: {len(eq_conditions)}")
        
        for i, eq in enumerate(eq_conditions):
            print(f"\nEQ {i}: {eq}")
            print(f"  Args: {eq.args}")
            
            left = eq.args.get('this') if 'this' in eq.args else eq.left
            right = eq.args.get('expression') if 'expression' in eq.args else eq.right
            
            print(f"  Left: {left} (type: {type(left)})")
            print(f"  Right: {right} (type: {type(right)})")
            
            # Column詳細
            if isinstance(left, exp.Column):
                print(f"    Left table: {left.table}, column: {left.name}")
            if isinstance(right, exp.Column):
                print(f"    Right table: {right.table}, column: {right.name}")

def debug_using():
    """USING句をデバッグ"""
    sql = """
    SELECT e.name, d.name
    FROM employees e
    JOIN departments d USING (dept_id)
    """
    
    print(f"\n=== USING Debug ===")
    print(f"SQL: {sql.strip()}")
    
    parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
    
    if 'joins' in parsed.args:
        joins = parsed.args['joins']
        
        for i, join in enumerate(joins):
            print(f"\nJoin {i}:")
            print(f"  Args: {join.args}")
            
            if 'using' in join.args:
                using = join.args['using']
                print(f"  USING: {using}")
                print(f"  USING type: {type(using)}")
                
                if isinstance(using, list):
                    print(f"  USING is list with {len(using)} items:")
                    for j, item in enumerate(using):
                        print(f"    Item {j}: {item} (type: {type(item)})")
                        if hasattr(item, 'name'):
                            print(f"      Name: {item.name}")

def test_analyzer_with_debug():
    """アナライザーでデバッグ"""
    print(f"\n=== Analyzer Debug ===")
    
    analyzer = SQLJoinAnalyzer()
    
    # FROM-WHERE のテスト
    sql1 = """
    SELECT c.name, o.total
    FROM customers c, orders o
    WHERE c.id = o.customer_id
    """
    
    print(f"Testing FROM-WHERE:")
    relationships1 = analyzer.analyze_sql(sql1)
    print(f"Relationships: {len(relationships1)}")
    for rel in relationships1:
        print(f"  {rel}")
    
    # USING のテスト
    sql2 = """
    SELECT e.name, d.name
    FROM employees e
    JOIN departments d USING (dept_id)
    """
    
    print(f"\nTesting USING:")
    relationships2 = analyzer.analyze_sql(sql2)
    print(f"Relationships: {len(relationships2)}")
    for rel in relationships2:
        print(f"  {rel}")

if __name__ == "__main__":
    debug_from_where()
    debug_using()
    test_analyzer_with_debug()