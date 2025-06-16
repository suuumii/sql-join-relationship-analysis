-- 在庫管理関連のクエリ
SELECT 
    p.product_id,
    p.product_name,
    p.sku,
    p.price,
    i.current_stock,
    i.reorder_level,
    w.warehouse_name,
    w.location as warehouse_location,
    s.supplier_name,
    s.contact_email,
    cat.category_name
FROM products p
LEFT JOIN inventory i ON p.product_id = i.product_id
LEFT JOIN warehouses w ON i.warehouse_id = w.warehouse_id
INNER JOIN suppliers s ON p.supplier_id = s.supplier_id
INNER JOIN categories cat ON p.category_id = cat.category_id
WHERE p.status = 'active'
  AND (i.current_stock <= i.reorder_level OR i.current_stock IS NULL);