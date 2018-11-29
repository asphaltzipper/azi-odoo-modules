
update mfg_work_header set name=t.new_name
from (
    select
        m.id,
        p.name as u_name,
        row_number() over (partition by m.work_date, p.name order by m.id) as row_num,
        m.work_date || ', ' || p.name || ', ' || row_number() over (partition by m.work_date, p.name order by m.id) as new_name
    from mfg_work_header as m
    left join res_users as u on u.id=m.work_user_id
    left join res_partner as p on p.id=u.partner_id
) as t
where t.id=mfg_work_header.id;

ALTER TABLE mfg_work_header ALTER COLUMN name SET NOT NULL;
