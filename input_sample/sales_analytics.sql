-- 売上分析関連のクエリ
SELECT 
    c.customer_id,
    c.customer_name,
    c.customer_type,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(oi.quantity * oi.unit_price) as total_sales,
    AVG(oi.quantity * oi.unit_price) as avg_order_value,
    MAX(o.order_date) as last_order_date,
    r.region_name,
    seg.segment_name
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN regions r ON c.region_id = r.region_id
LEFT JOIN customer_segments seg ON c.segment_id = seg.segment_id
WHERE c.status = 'active'
GROUP BY c.customer_id, c.customer_name, c.customer_type, r.region_name, seg.segment_name
HAVING total_sales > 1000
ORDER BY total_sales DESC;