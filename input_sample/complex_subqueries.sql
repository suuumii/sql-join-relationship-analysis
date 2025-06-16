-- 複雑なサブクエリを含むクエリ
SELECT 
    main_data.customer_id,
    main_data.customer_name,
    main_data.total_orders,
    monthly_stats.avg_monthly_sales,
    product_preferences.top_category,
    loyalty_info.loyalty_level
FROM (
    SELECT 
        c.customer_id,
        c.customer_name,
        COUNT(o.order_id) as total_orders
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE c.status = 'active'
    GROUP BY c.customer_id, c.customer_name
) main_data
LEFT JOIN (
    SELECT 
        o.customer_id,
        AVG(monthly_total) as avg_monthly_sales
    FROM (
        SELECT 
            o.customer_id,
            DATE_TRUNC('month', o.order_date) as order_month,
            SUM(oi.quantity * oi.unit_price) as monthly_total
        FROM orders o
        INNER JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY o.customer_id, DATE_TRUNC('month', o.order_date)
    ) monthly_data
    GROUP BY o.customer_id
) monthly_stats ON main_data.customer_id = monthly_stats.customer_id
LEFT JOIN (
    SELECT DISTINCT
        c.customer_id,
        FIRST_VALUE(cat.category_name) OVER (
            PARTITION BY c.customer_id 
            ORDER BY category_sales DESC
        ) as top_category
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN categories cat ON p.category_id = cat.category_id
    JOIN (
        SELECT 
            c.customer_id,
            cat.category_id,
            SUM(oi.quantity * oi.unit_price) as category_sales
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN categories cat ON p.category_id = cat.category_id
        GROUP BY c.customer_id, cat.category_id
    ) cat_totals ON c.customer_id = cat_totals.customer_id 
                  AND cat.category_id = cat_totals.category_id
) product_preferences ON main_data.customer_id = product_preferences.customer_id
LEFT JOIN (
    SELECT 
        cl.customer_id,
        ll.level_name as loyalty_level
    FROM customer_loyalty cl
    JOIN loyalty_levels ll ON cl.level_id = ll.level_id
) loyalty_info ON main_data.customer_id = loyalty_info.customer_id
WHERE main_data.total_orders >= 5;