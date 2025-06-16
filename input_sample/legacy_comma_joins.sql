-- レガシーなカンマ結合を使用したクエリ
SELECT 
    o.order_id,
    c.customer_name,
    p.product_name,
    oi.quantity,
    s.supplier_name,
    w.warehouse_name
FROM orders o, 
     customers c, 
     order_items oi, 
     products p, 
     suppliers s,
     warehouses w,
     inventory i
WHERE o.customer_id = c.customer_id
  AND o.order_id = oi.order_id
  AND oi.product_id = p.product_id
  AND p.supplier_id = s.supplier_id
  AND p.product_id = i.product_id
  AND i.warehouse_id = w.warehouse_id
  AND o.status = 'shipped'
  AND c.region = 'North America';