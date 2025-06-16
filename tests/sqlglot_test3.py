#!/usr/bin/env python3
"""
sqlglotの構造を詳しく調べる
"""

import sqlglot
import sqlglot.expressions as exp

def inspect_join_structure():
    """JOIN構造を詳しく調べる"""
    sql = """
    SELECT u.name, p.title
    FROM users u
    JOIN posts p ON u.id = p.user_id
    """
    
    print("=== Detailed JOIN Structure ===")
    
    parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
    
    print(f"Parsed object attributes:")
    for attr in dir(parsed):
        if not attr.startswith('_'):
            try:
                value = getattr(parsed, attr)
                if not callable(value):
                    print(f"  {attr}: {value}")
            except:
                pass
    
    print(f"\nParsed args: {parsed.args}")
    
    # 特に'joins'を確認
    if 'joins' in parsed.args:
        joins = parsed.args['joins']
        print(f"\nJoins from args: {joins}")
        print(f"Joins type: {type(joins)}")
        print(f"Joins length: {len(joins) if joins else 0}")
        
        if joins:
            for i, join in enumerate(joins):
                print(f"\n  JOIN {i}:")
                print(f"    Object: {join}")
                print(f"    Type: {type(join)}")
                print(f"    Args: {join.args}")
                
                # 各種プロパティを確認
                for attr in ['this', 'on', 'using', 'kind']:
                    if hasattr(join, attr):
                        value = getattr(join, attr)
                        print(f"    {attr}: {value}")
    
    # joins プロパティも確認
    if hasattr(parsed, 'joins'):
        print(f"\nJoins property: {parsed.joins}")

def inspect_from_structure():
    """FROM句の構造を調べる"""
    sql = """
    SELECT c.name, o.total
    FROM customers c, orders o
    WHERE c.id = o.customer_id
    """
    
    print(f"\n=== FROM Structure ===")
    
    parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
    
    print(f"Parsed args: {parsed.args}")
    
    # FROM句を詳しく調べる
    if 'from' in parsed.args:
        from_clause = parsed.args['from']
        print(f"\nFROM clause: {from_clause}")
        print(f"FROM type: {type(from_clause)}")
        print(f"FROM args: {from_clause.args}")
        
        # FROM句の中身を詳しく見る
        for attr in ['this', 'expressions']:
            if hasattr(from_clause, attr):
                value = getattr(from_clause, attr)
                print(f"  {attr}: {value}")
    
    # joinsも確認（FROM句の複数テーブルがJOINに変換される場合）
    if 'joins' in parsed.args:
        joins = parsed.args['joins']
        print(f"\nJoins (from comma-separated): {joins}")

def test_alternative_parsing():
    """別の方法でパースしてみる"""
    sql1 = """
    SELECT u.name, p.title
    FROM users u
    JOIN posts p ON u.id = p.user_id
    """
    
    sql2 = """
    SELECT c.name, o.total
    FROM customers c, orders o
    WHERE c.id = o.customer_id
    """
    
    print(f"\n=== Alternative Parsing ===")
    
    for i, sql in enumerate([sql1, sql2], 1):
        print(f"\nSQL {i}: {sql.strip()}")
        
        # 異なる方法でパース
        parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
        
        # すべてのJOINを探す
        all_joins = list(parsed.find_all(exp.Join))
        print(f"All joins found: {len(all_joins)}")
        
        for j, join in enumerate(all_joins):
            print(f"  JOIN {j}: {join}")
        
        # すべてのテーブルを探す
        all_tables = list(parsed.find_all(exp.Table))
        print(f"All tables found: {len(all_tables)}")
        
        for j, table in enumerate(all_tables):
            print(f"  TABLE {j}: {table}")
            if hasattr(table, 'name'):
                print(f"    Name: {table.name}")
            if hasattr(table, 'alias'):
                print(f"    Alias: {table.alias}")

if __name__ == "__main__":
    inspect_join_structure()
    inspect_from_structure()
    test_alternative_parsing()