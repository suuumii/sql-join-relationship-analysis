-- 従業員階層関連のクエリ
SELECT 
    emp.employee_id,
    emp.employee_name,
    emp.email,
    emp.hire_date,
    emp.salary,
    dept.department_name,
    mgr.employee_name as manager_name,
    pos.position_title,
    loc.location_name,
    loc.address
FROM employees emp
INNER JOIN departments dept USING (department_id)
LEFT JOIN employees mgr ON emp.manager_id = mgr.employee_id
INNER JOIN positions pos ON emp.position_id = pos.position_id
LEFT JOIN locations loc ON dept.location_id = loc.location_id
WHERE emp.status = 'active'
ORDER BY dept.department_name, emp.employee_name;