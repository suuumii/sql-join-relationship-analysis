#!/usr/bin/env python3
"""
テスト用のサンプルSELECTクエリ集
様々なJOINパターンとケースをテスト
"""

# EC サイトのサンプルクエリ
ECOMMERCE_QUERIES = [
    # 基本的なINNER JOIN
    """
    SELECT 
        u.user_id,
        u.username,
        u.email,
        o.order_id,
        o.order_date,
        o.total_amount
    FROM users u
    INNER JOIN orders o ON u.user_id = o.user_id
    WHERE u.status = 'active'
    AND o.order_date >= '2023-01-01'
    """,
    
    # 複数テーブルのJOIN
    """
    SELECT 
        c.customer_name,
        o.order_id,
        p.product_name,
        oi.quantity,
        oi.unit_price,
        cat.category_name
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN categories cat ON p.category_id = cat.category_id
    WHERE o.status = 'completed'
    """,
    
    # LEFT JOINを含む複合クエリ
    """
    SELECT 
        u.username,
        u.email,
        p.first_name,
        p.last_name,
        a.street_address,
        a.city,
        a.postal_code
    FROM users u
    LEFT JOIN profiles p ON u.user_id = p.user_id
    LEFT JOIN addresses a ON u.user_id = a.user_id AND a.address_type = 'billing'
    WHERE u.created_at >= '2022-01-01'
    """,
    
    # FROM句に複数テーブル + WHERE条件
    """
    SELECT 
        o.order_id,
        c.customer_name,
        p.product_name,
        s.supplier_name,
        oi.quantity
    FROM orders o, customers c, order_items oi, products p, suppliers s
    WHERE o.customer_id = c.customer_id
    AND o.order_id = oi.order_id
    AND oi.product_id = p.product_id
    AND p.supplier_id = s.supplier_id
    AND o.order_date BETWEEN '2023-01-01' AND '2023-12-31'
    """,
]

# ブログシステムのサンプルクエリ
BLOG_QUERIES = [
    # USING句を使用
    """
    SELECT 
        p.title,
        p.content,
        u.username,
        c.category_name
    FROM posts p
    JOIN users u USING (user_id)
    JOIN categories c USING (category_id)
    WHERE p.published = 1
    """,
    
    # サブクエリ内のJOIN
    """
    SELECT 
        u.username,
        u.email,
        post_stats.total_posts,
        post_stats.avg_views
    FROM users u
    LEFT JOIN (
        SELECT 
            p.user_id,
            COUNT(*) as total_posts,
            AVG(p.view_count) as avg_views
        FROM posts p
        JOIN categories c ON p.category_id = c.category_id
        WHERE c.active = 1 AND p.published = 1
        GROUP BY p.user_id
    ) post_stats ON u.user_id = post_stats.user_id
    """,
    
    # NATURAL JOIN
    """
    SELECT 
        e.employee_name,
        e.email,
        d.department_name,
        d.budget
    FROM employees e
    NATURAL JOIN departments d
    WHERE e.status = 'active'
    """,
    
    # 自己結合（Self JOIN）
    """
    SELECT 
        emp.employee_name as employee,
        mgr.employee_name as manager,
        emp.hire_date,
        mgr.hire_date as manager_hire_date
    FROM employees emp
    LEFT JOIN employees mgr ON emp.manager_id = mgr.employee_id
    WHERE emp.status = 'active'
    """,
]

# 複雑なクエリ
COMPLEX_QUERIES = [
    # 複数のサブクエリとJOIN
    """
    SELECT 
        main_data.user_id,
        main_data.username,
        main_data.email,
        recent_posts.post_count as recent_posts,
        all_posts.total_posts,
        comment_stats.total_comments
    FROM (
        SELECT u.user_id, u.username, u.email
        FROM users u
        WHERE u.status = 'active' AND u.created_at >= '2020-01-01'
    ) main_data
    LEFT JOIN (
        SELECT 
            p.user_id,
            COUNT(*) as post_count
        FROM posts p
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        AND c.active = 1
        GROUP BY p.user_id
    ) recent_posts ON main_data.user_id = recent_posts.user_id
    LEFT JOIN (
        SELECT user_id, COUNT(*) as total_posts
        FROM posts
        WHERE published = 1
        GROUP BY user_id
    ) all_posts ON main_data.user_id = all_posts.user_id
    LEFT JOIN (
        SELECT 
            p.user_id,
            COUNT(c.comment_id) as total_comments
        FROM posts p
        LEFT JOIN comments c ON p.post_id = c.post_id
        GROUP BY p.user_id
    ) comment_stats ON main_data.user_id = comment_stats.user_id
    """,
    
    # 複数のJOIN種類を組み合わせ
    """
    SELECT 
        o.order_id,
        c.customer_name,
        p.product_name,
        cat.category_name,
        s.supplier_name,
        r.rating,
        r.review_text
    FROM orders o
    INNER JOIN customers c ON o.customer_id = c.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    INNER JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN categories cat ON p.category_id = cat.category_id
    RIGHT JOIN suppliers s ON p.supplier_id = s.supplier_id
    LEFT JOIN reviews r ON p.product_id = r.product_id AND r.customer_id = c.customer_id
    WHERE o.status IN ('completed', 'shipped')
    AND o.order_date >= '2023-01-01'
    """,
    
    # UNION with JOINs
    """
    SELECT 'current' as period, u.username, COUNT(o.order_id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id 
    WHERE o.order_date >= '2024-01-01'
    GROUP BY u.user_id, u.username
    UNION ALL
    SELECT 'previous' as period, u.username, COUNT(o.order_id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    WHERE o.order_date >= '2023-01-01' AND o.order_date < '2024-01-01'
    GROUP BY u.user_id, u.username
    """,
]

# エラーテスト用クエリ
ERROR_TEST_QUERIES = [
    # 不正なSQL構文
    """
    SELECT * FROM users u
    JOIN posts p ON u.id = 
    """,
    
    # 空のクエリ
    "",
    
    # 単純なSELECT（JOINなし）
    """
    SELECT * FROM users WHERE status = 'active'
    """,
]

# 全テストクエリをまとめる
ALL_TEST_QUERIES = {
    'ecommerce': ECOMMERCE_QUERIES,
    'blog': BLOG_QUERIES,
    'complex': COMPLEX_QUERIES,
    'error_tests': ERROR_TEST_QUERIES
}

def get_all_valid_queries():
    """エラーテスト以外の全クエリを取得"""
    queries = []
    queries.extend(ECOMMERCE_QUERIES)
    queries.extend(BLOG_QUERIES)
    queries.extend(COMPLEX_QUERIES)
    return queries

def get_queries_by_category(category):
    """カテゴリ別にクエリを取得"""
    return ALL_TEST_QUERIES.get(category, [])

if __name__ == "__main__":
    print("=== サンプルクエリ統計 ===")
    for category, queries in ALL_TEST_QUERIES.items():
        print(f"{category}: {len(queries)} クエリ")
    
    total_queries = sum(len(queries) for queries in ALL_TEST_QUERIES.values())
    print(f"合計: {total_queries} クエリ")