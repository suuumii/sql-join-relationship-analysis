#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_join_analyzer import SQLJoinAnalyzer

def test_complex_queries():
    """Test the analyzer with various complex SQL queries"""
    analyzer = SQLJoinAnalyzer()
    
    # Test cases covering different JOIN scenarios
    test_queries = [
        # Standard INNER JOIN
        """
        SELECT u.name, p.title, c.name as category_name
        FROM users u
        INNER JOIN posts p ON u.id = p.user_id
        INNER JOIN categories c ON p.category_id = c.id
        WHERE u.active = 1 AND p.published = 1
        """,
        
        # LEFT JOIN with subquery
        """
        SELECT u.name, u.email, recent_posts.post_count
        FROM users u
        LEFT JOIN (
            SELECT user_id, COUNT(*) as post_count
            FROM posts 
            WHERE created_at > '2023-01-01'
            GROUP BY user_id
        ) recent_posts ON u.id = recent_posts.user_id
        """,
        
        # Multiple tables in FROM with WHERE conditions
        """
        SELECT o.order_id, c.customer_name, p.product_name, oi.quantity
        FROM orders o, customers c, products p, order_items oi
        WHERE o.customer_id = c.customer_id 
          AND oi.order_id = o.order_id
          AND oi.product_id = p.product_id
          AND o.order_date > '2023-01-01'
        """,
        
        # USING clause
        """
        SELECT e.employee_name, d.department_name
        FROM employees e
        JOIN departments d USING (department_id)
        """,
        
        # NATURAL JOIN
        """
        SELECT *
        FROM employees
        NATURAL JOIN department_info
        """,
        
        # Complex nested query with multiple JOINs
        """
        SELECT 
            main.user_id,
            main.username,
            stats.total_posts,
            recent.recent_posts
        FROM (
            SELECT u.id as user_id, u.username
            FROM users u
            WHERE u.status = 'active'
        ) main
        LEFT JOIN (
            SELECT 
                p.user_id,
                COUNT(*) as total_posts
            FROM posts p
            JOIN categories c ON p.category_id = c.id
            WHERE c.active = 1
            GROUP BY p.user_id
        ) stats ON main.user_id = stats.user_id
        LEFT JOIN (
            SELECT 
                user_id,
                COUNT(*) as recent_posts
            FROM posts
            WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY user_id
        ) recent ON main.user_id = recent.user_id
        """,
        
        # Self JOIN
        """
        SELECT 
            e1.employee_name as employee,
            e2.employee_name as manager
        FROM employees e1
        LEFT JOIN employees e2 ON e1.manager_id = e2.employee_id
        """,
        
        # Multiple JOIN types in one query
        """
        SELECT 
            o.order_id,
            c.customer_name,
            p.product_name,
            cat.category_name,
            s.supplier_name
        FROM orders o
        INNER JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        INNER JOIN products p ON oi.product_id = p.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        RIGHT JOIN suppliers s ON p.supplier_id = s.id
        WHERE o.status = 'completed'
        """
    ]
    
    print("=== Testing SQL JOIN Analyzer ===\n")
    
    # Analyze each query individually
    for i, query in enumerate(test_queries, 1):
        print(f"--- Test Query {i} ---")
        print("SQL:")
        print(query.strip())
        print("\nRelationships found:")
        
        relationships = analyzer.analyze_sql(query)
        
        if relationships:
            for rel in relationships:
                print(f"  {rel['table1']}.{rel['column1']} ({rel['column_definition1']}) -> "
                      f"{rel['table2']}.{rel['column2']} ({rel['column_definition2']})")
        else:
            print("  No relationships found")
        
        print("\n" + "="*50 + "\n")
    
    # Analyze all queries together
    print("=== Combined Analysis ===")
    all_relationships = analyzer.analyze_multiple_queries(test_queries)
    
    print(f"Total unique relationships found: {len(all_relationships)}")
    
    # Export results
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    csv_file = os.path.join(output_dir, 'example_relationships.csv')
    analyzer.export_to_csv(csv_file)
    print(f"Results exported to {csv_file}")
    
    # Generate visualization
    try:
        graph_file = os.path.join(output_dir, 'example_relationships_graph.png')
        analyzer.generate_graph_visualization(graph_file)
        print(f"Graph visualization saved as {graph_file}")
    except Exception as e:
        print(f"Could not generate visualization: {e}")
    
    return all_relationships

if __name__ == "__main__":
    test_complex_queries()