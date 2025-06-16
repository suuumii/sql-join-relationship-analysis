-- ユーザー管理関連のクエリ
SELECT 
    u.user_id,
    u.username,
    u.email,
    p.first_name,
    p.last_name,
    p.phone_number,
    r.role_name
FROM users u
LEFT JOIN profiles p ON u.user_id = p.user_id
INNER JOIN user_roles ur ON u.user_id = ur.user_id
INNER JOIN roles r ON ur.role_id = r.role_id
WHERE u.status = 'active'
  AND u.created_at >= '2023-01-01'
ORDER BY u.username;