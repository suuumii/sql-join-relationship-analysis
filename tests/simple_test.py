#!/usr/bin/env python3
"""
Simple test to verify basic functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_join_analyzer import SQLJoinAnalyzer

def simple_test():
    """Basic functionality test"""
    print("=== Simple Test ===")
    
    analyzer = SQLJoinAnalyzer()
    
    # Very basic test query
    test_sql = """
    SELECT u.name, p.title
    FROM users u
    JOIN posts p ON u.id = p.user_id
    """
    
    print("Testing SQL:")
    print(test_sql.strip())
    
    try:
        relationships = analyzer.analyze_sql(test_sql)
        print(f"\nFound {len(relationships)} relationships:")
        
        for rel in relationships:
            print(f"  {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")
        
        # Test CSV export
        analyzer.export_to_csv('simple_test.csv')
        print("\nCSV exported successfully")
        
        # Read and display CSV content
        try:
            with open('simple_test.csv', 'r', encoding='utf-8') as f:
                print("\nCSV Content:")
                print(f.read())
        except Exception as e:
            print(f"Error reading CSV: {e}")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_queries():
    """Test multiple simple queries"""
    print("\n=== Multiple Queries Test ===")
    
    analyzer = SQLJoinAnalyzer()
    
    queries = [
        """
        SELECT u.name, p.title
        FROM users u
        JOIN posts p ON u.id = p.user_id
        """,
        
        """
        SELECT c.name, o.total
        FROM customers c, orders o
        WHERE c.id = o.customer_id
        """,
        
        """
        SELECT e.name, d.name
        FROM employees e
        JOIN departments d USING (dept_id)
        """
    ]
    
    for i, sql in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        print(sql.strip())
        
        try:
            relationships = analyzer.analyze_sql(sql)
            print(f"Relationships: {len(relationships)}")
            
            for rel in relationships:
                if rel['table1'] and rel['table2']:
                    print(f"  {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")
                    
        except Exception as e:
            print(f"Error in query {i}: {e}")

if __name__ == "__main__":
    success = simple_test()
    if success:
        test_multiple_queries()
        print("\n=== Test Complete ===")
    else:
        print("\n=== Test Failed ===")