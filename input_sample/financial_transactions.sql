-- 金融取引関連のクエリ
SELECT 
    t.transaction_id,
    t.transaction_date,
    t.amount,
    t.transaction_type,
    acc.account_number,
    acc.account_type,
    cust.customer_name,
    cust.customer_type,
    branch.branch_name,
    branch.branch_code,
    emp.employee_name as processed_by
FROM transactions t
INNER JOIN accounts acc ON t.account_id = acc.account_id
INNER JOIN customers cust ON acc.customer_id = cust.customer_id
LEFT JOIN branches branch ON t.branch_id = branch.branch_id
LEFT JOIN employees emp ON t.processed_by = emp.employee_id
WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
  AND t.status = 'completed'
  AND t.amount > 1000
ORDER BY t.transaction_date DESC, t.amount DESC;