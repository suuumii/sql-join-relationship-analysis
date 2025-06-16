#!/usr/bin/env python3
"""
自己結合の問題をデバッグ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlglot
import sqlglot.expressions as exp
from sql_join_analyzer import SQLJoinAnalyzer

def debug_self_join():
    """自己結合のデバッグ"""
    sql = """
    SELECT 
        e1.employee_name as employee,
        e2.employee_name as manager
    FROM employees e1
    LEFT JOIN employees e2 ON e1.manager_id = e2.employee_id
    """
    
    print("=== Self JOIN Debug ===")
    print(f"SQL: {sql.strip()}")
    
    parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
    
    print(f"\nParsed args: {list(parsed.args.keys())}")
    
    if 'joins' in parsed.args:
        joins = parsed.args['joins']
        print(f"Joins: {len(joins)}")
        
        for i, join in enumerate(joins):
            print(f"\nJoin {i}:")
            print(f"  Object: {join}")
            print(f"  Args: {join.args}")
            
            if 'on' in join.args:
                on_condition = join.args['on']
                print(f"  ON: {on_condition}")
                print(f"  ON type: {type(on_condition)}")
                print(f"  ON args: {on_condition.args}")
                
                # EQ条件の詳細
                left = on_condition.args.get('this')
                right = on_condition.args.get('expression')
                
                print(f"    Left: {left} (type: {type(left)})")
                print(f"    Right: {right} (type: {type(right)})")
                
                if isinstance(left, exp.Column):
                    print(f"      Left table: {left.table}, column: {left.name}")
                if isinstance(right, exp.Column):
                    print(f"      Right table: {right.table}, column: {right.name}")

def test_analyzer_self_join():
    """アナライザーでの自己結合テスト"""
    print(f"\n=== Analyzer Self JOIN Test ===")
    
    analyzer = SQLJoinAnalyzer()
    
    sql = """
    SELECT 
        e1.employee_name as employee,
        e2.employee_name as manager
    FROM employees e1
    LEFT JOIN employees e2 ON e1.manager_id = e2.employee_id
    """
    
    print(f"Testing self join:")
    relationships = analyzer.analyze_sql(sql)
    print(f"Relationships found: {len(relationships)}")
    
    for rel in relationships:
        print(f"  {rel}")

def test_variations():
    """様々な自己結合のバリエーションをテスト"""
    print(f"\n=== Self JOIN Variations ===")
    
    analyzer = SQLJoinAnalyzer()
    
    variations = [
        # バリエーション1: シンプルな自己結合
        """
        SELECT e1.name, e2.name
        FROM employees e1
        JOIN employees e2 ON e1.manager_id = e2.id
        """,
        
        # バリエーション2: 異なるカラム名
        """
        SELECT emp.name, mgr.name
        FROM employees emp
        LEFT JOIN employees mgr ON emp.supervisor_id = mgr.employee_id
        """,
        
        # バリエーション3: 同じテーブル名での結合
        """
        SELECT a.name, b.name
        FROM users a
        JOIN users b ON a.parent_id = b.user_id
        """
    ]
    
    for i, sql in enumerate(variations, 1):
        print(f"\nVariation {i}:")
        print(sql.strip())
        
        relationships = analyzer.analyze_sql(sql)
        print(f"Relationships: {len(relationships)}")
        for rel in relationships:
            print(f"  {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")

if __name__ == "__main__":
    debug_self_join()
    test_analyzer_self_join()
    test_variations()