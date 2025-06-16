#!/usr/bin/env python3
"""
可視化機能のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sql_join_analyzer import SQLJoinAnalyzer

def test_graph_visualization():
    """グラフ可視化のテスト"""
    print("=== Graph Visualization Test ===")
    
    analyzer = SQLJoinAnalyzer()
    
    # 複数のクエリで関係を作成
    queries = [
        """
        SELECT u.name, p.title, c.name as category
        FROM users u
        JOIN posts p ON u.id = p.user_id
        JOIN categories c ON p.category_id = c.id
        WHERE u.active = 1
        """,
        
        """
        SELECT o.id, o.total, c.name, p.name
        FROM orders o, customers c, products p
        WHERE o.customer_id = c.id AND o.product_id = p.id
        """,
        
        """
        SELECT e.name, d.name
        FROM employees e
        JOIN departments d USING (dept_id)
        """,
        
        """
        SELECT emp.name as employee, mgr.name as manager
        FROM employees emp
        LEFT JOIN employees mgr ON emp.manager_id = mgr.id
        """
    ]
    
    print(f"Analyzing {len(queries)} queries...")
    
    # 複数クエリの解析
    all_relationships = analyzer.analyze_multiple_queries(queries)
    
    print(f"Found {len(all_relationships)} unique relationships:")
    for i, rel in enumerate(all_relationships, 1):
        if rel['table1'] and rel['table2']:
            print(f"  {i}. {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")
    
    # CSV出力
    csv_file = 'test_visualization_output.csv'
    analyzer.export_to_csv(csv_file)
    print(f"\nCSV exported to: {csv_file}")
    
    # グラフ可視化の生成
    try:
        graph_file = 'test_visualization_graph.png'
        analyzer.generate_graph_visualization(graph_file)
        print(f"Graph visualization saved to: {graph_file}")
        
        # グラフ情報を表示
        if hasattr(analyzer, 'graph') and analyzer.graph.nodes():
            print(f"\nGraph nodes: {list(analyzer.graph.nodes())}")
            print(f"Graph edges: {list(analyzer.graph.edges())}")
        
        return True
        
    except Exception as e:
        print(f"Graph generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_csv_content():
    """CSV内容の詳細確認"""
    print(f"\n=== CSV Content Test ===")
    
    try:
        with open('test_visualization_output.csv', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("CSV Content:")
        print(content)
        
        lines = content.strip().split('\n')
        print(f"\nCSV Statistics:")
        print(f"  Total lines: {len(lines)}")
        print(f"  Header: {lines[0] if lines else 'None'}")
        print(f"  Data rows: {len(lines) - 1 if len(lines) > 1 else 0}")
        
    except Exception as e:
        print(f"Error reading CSV: {e}")

if __name__ == "__main__":
    success = test_graph_visualization()
    test_csv_content()
    
    if success:
        print(f"\n=== Visualization Test PASSED ===")
    else:
        print(f"\n=== Visualization Test FAILED ===")