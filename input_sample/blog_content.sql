-- ブログコンテンツ関連のクエリ
SELECT 
    p.post_id,
    p.title,
    p.content_preview,
    p.published_date,
    p.view_count,
    u.username as author,
    u.display_name,
    cat.category_name,
    COUNT(c.comment_id) as comment_count,
    AVG(r.rating) as avg_rating,
    STRING_AGG(t.tag_name, ', ') as tags
FROM posts p
INNER JOIN users u ON p.author_id = u.user_id
LEFT JOIN categories cat ON p.category_id = cat.category_id
LEFT JOIN comments c ON p.post_id = c.post_id AND c.status = 'approved'
LEFT JOIN ratings r ON p.post_id = r.post_id
LEFT JOIN post_tags pt ON p.post_id = pt.post_id
LEFT JOIN tags t ON pt.tag_id = t.tag_id
WHERE p.status = 'published'
  AND p.published_date >= '2023-01-01'
GROUP BY p.post_id, p.title, p.content_preview, p.published_date, 
         p.view_count, u.username, u.display_name, cat.category_name
ORDER BY p.published_date DESC;