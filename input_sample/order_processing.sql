-- 注文処理関連のクエリ
SELECT 
    o.order_id,
    o.order_date,
    c.customer_name,
    c.email as customer_email,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    (oi.quantity * oi.unit_price) as line_total,
    cat.category_name,
    s.supplier_name
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
LEFT JOIN categories cat ON p.category_id = cat.category_id
LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
WHERE o.status IN ('processing', 'shipped', 'completed')
  AND o.order_date BETWEEN '2023-01-01' AND '2023-12-31';