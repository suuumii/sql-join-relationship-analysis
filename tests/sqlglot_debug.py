#!/usr/bin/env python3
"""
sqlglotの動作確認とデバッグ
"""

import sqlglot
import sqlglot.expressions as exp

def debug_sqlglot():
    """sqlglotのASTを確認"""
    sql = """
    SELECT u.name, p.title
    FROM users u
    JOIN posts p ON u.id = p.user_id
    """
    
    print("=== SQLGlot Debug ===")
    print(f"SQL: {sql.strip()}")
    
    try:
        # Parse with MySQL dialect
        parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
        
        print(f"\nParsed type: {type(parsed)}")
        print(f"Parsed repr: {repr(parsed)}")
        
        # Print AST structure
        print(f"\nAST Structure:")
        print(parsed.sql(pretty=True))
        
        # Find all nodes
        print(f"\nAll node types:")
        for node in parsed.walk():
            print(f"  {type(node).__name__}: {repr(node)}")
        
        # Find JOIN nodes specifically
        print(f"\nJOIN nodes:")
        joins = list(parsed.find_all(exp.Join))
        print(f"Found {len(joins)} JOIN nodes")
        
        for i, join in enumerate(joins):
            print(f"  JOIN {i+1}:")
            print(f"    Type: {type(join)}")
            print(f"    This: {join.this}")
            print(f"    On: {join.on}")
            print(f"    Kind: {getattr(join, 'kind', 'None')}")
            
            # Get table name from join
            if hasattr(join, 'this') and join.this:
                print(f"    Table: {join.this}")
                if hasattr(join.this, 'name'):
                    print(f"    Table name: {join.this.name}")
        
        # Find FROM clause
        print(f"\nFROM clause:")
        from_clause = parsed.find(exp.From)
        if from_clause:
            print(f"  FROM: {from_clause}")
            if hasattr(from_clause, 'expressions'):
                for expr in from_clause.expressions:
                    print(f"    Expression: {expr}")
        
        # Find WHERE clause
        print(f"\nWHERE clause:")
        where_clause = parsed.find(exp.Where)
        if where_clause:
            print(f"  WHERE: {where_clause}")
        
        return parsed
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def debug_where_query():
    """WHERE句でのJOIN条件をデバッグ"""
    sql = """
    SELECT c.name, o.total
    FROM customers c, orders o
    WHERE c.id = o.customer_id
    """
    
    print(f"\n=== WHERE Query Debug ===")
    print(f"SQL: {sql.strip()}")
    
    try:
        parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
        
        print(f"\nFROM clause:")
        from_clause = parsed.find(exp.From)
        if from_clause:
            print(f"  FROM: {from_clause}")
            if hasattr(from_clause, 'expressions'):
                print(f"  Number of expressions: {len(from_clause.expressions)}")
                for i, expr in enumerate(from_clause.expressions):
                    print(f"    Expression {i}: {expr} (type: {type(expr)})")
                    if hasattr(expr, 'name'):
                        print(f"      Name: {expr.name}")
                    if hasattr(expr, 'alias'):
                        print(f"      Alias: {expr.alias}")
        
        print(f"\nWHERE clause:")
        where_clause = parsed.find(exp.Where)
        if where_clause:
            print(f"  WHERE: {where_clause}")
            
            # Find equality conditions
            equalities = list(where_clause.find_all(exp.EQ))
            print(f"  Equalities found: {len(equalities)}")
            
            for i, eq in enumerate(equalities):
                print(f"    EQ {i}: {eq}")
                print(f"      Left: {eq.left} (type: {type(eq.left)})")
                print(f"      Right: {eq.right} (type: {type(eq.right)})")
                
                # Check if these are column references
                if hasattr(eq.left, 'table') and hasattr(eq.left, 'name'):
                    print(f"      Left table: {eq.left.table}, column: {eq.left.name}")
                if hasattr(eq.right, 'table') and hasattr(eq.right, 'name'):
                    print(f"      Right table: {eq.right.table}, column: {eq.right.name}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def debug_using_query():
    """USING句をデバッグ"""
    sql = """
    SELECT e.name, d.name
    FROM employees e
    JOIN departments d USING (dept_id)
    """
    
    print(f"\n=== USING Query Debug ===")
    print(f"SQL: {sql.strip()}")
    
    try:
        parsed = sqlglot.parse_one(sql, dialect=sqlglot.dialects.MySQL)
        
        joins = list(parsed.find_all(exp.Join))
        print(f"JOINs found: {len(joins)}")
        
        for i, join in enumerate(joins):
            print(f"  JOIN {i}:")
            print(f"    This: {join.this}")
            print(f"    On: {join.on}")
            print(f"    Using: {getattr(join, 'using', 'None')}")
            
            if hasattr(join, 'using') and join.using:
                print(f"    Using clause: {join.using}")
                if hasattr(join.using, 'expressions'):
                    for expr in join.using.expressions:
                        print(f"      Column: {expr}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sqlglot()
    debug_where_query()
    debug_using_query()