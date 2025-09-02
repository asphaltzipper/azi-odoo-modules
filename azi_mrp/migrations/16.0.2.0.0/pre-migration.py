import io, csv
import logging

_logger = logging.getLogger(__name__)


def migrate(env, version):
    _logger.info("Transforming bom history data to adjacency list model")

    env.execute("""
        select distinct on (mrp_production_id)
            mbh.id,
            mbh.mrp_production_id as production_id,
            mp.product_id,
            mbh.create_date,
            mbh.create_uid,
            mbh.write_date,
            mbh.write_uid
        from mrp_bom_history mbh
        left join mrp_production mp on mp.id=mbh.mrp_production_id
        where mbh.mrp_production_id is not null
        order by mbh.mrp_production_id
    """)
    mo_keys = [
        "id",
        "production_id",
        "product_id",
        "create_date",
        "create_uid",
        "write_date",
        "write_uid",
    ]
    mos = [dict(zip(mo_keys, row)) for row in env.fetchall()]

    line_sql = """
        select
            mbhl.product_id,
            mbhl.product_qty,
            coalesce(mbhl.product_uom_id, pt.uom_id) as product_uom_id,
            mbhl.sequence+1 as level,
            mbhl.id as sequence
        from mrp_bom_history_line_upgrade mbhl
        left join product_product pp on pp.id=mbhl.product_id
        left join product_template pt on pt.id=pp.product_tmpl_id
        where mbhl.bom_history_id=%s
        order by mbhl.id
    """
    line_keys = [
        "product_id",
        "product_qty",
        "product_uom_id",
        "level",
        "sequence",
    ]

    copy_sql = """
        COPY mrp_bom_history_line (
            production_id,
            parent_product_id,
            product_id,
            product_qty,
            product_uom_id,
            create_date,
            create_uid,
            write_date,
            write_uid
        ) FROM STDIN
    """

    insert_sql = """
        insert into mrp_bom_history_line (
            production_id,
            parent_product_id,
            product_id,
            product_qty,
            product_uom_id,
            create_date,
            create_uid,
            write_date,
            write_uid
        ) values 
    """
    values_sql = "(%s,%s,%s,%s,%s,'%s',%s,'%s',%s)"

    # populate adjacency data
    for mo in mos:
        env.execute(line_sql, (mo['id'],))
        lines = [dict(zip(line_keys, row)) for row in env.fetchall()]
        # put the MO finished product at level zero
        parent_stack = [{
            'product_id': mo['product_id'],
            'level': 0,
        }]
        adjacencies = {}
        vals_string = ""
        for line in lines:
            parent_stack = parent_stack[0:line['level']]
            if not adjacencies.get(
                    (parent_stack[-1]['product_id'], line['product_id'])):
                adjacencies[(parent_stack[-1]['product_id'], line['product_id'])] = 1
                vals = (
                    mo['production_id'],
                    parent_stack[-1]['product_id'],
                    line['product_id'],
                    line['product_qty'],
                    line['product_uom_id'],
                    mo['create_date'],
                    mo['create_uid'],
                    mo['write_date'],
                    mo['write_uid'],
                )
                if vals_string:
                    vals_string = vals_string + ","
                vals_string = vals_string + values_sql % vals
            parent_stack.append({
                'product_id': line['product_id'],
                'level': line['level'],
            })
        _logger.info("Inserting line data for MO %s" % mo['production_id'])
        # psycopg2 doesn't have the copy() function like psycopg3
        # with env.copy(copy_sql) as copy:
        #     for record in line_vals_list:
        #         copy.write_row(tuple(record))
        # env.commit()
        # also tried io buffer, csv, and the copy_from() function, but copy_from isn't
        # exposed in Odoo
        # executemany() is slow
        #env.executemany(insert_sql, tuple(line_vals_list))
        # building a single insert query is faster for large BOMs
        env.execute(insert_sql+vals_string)


    # add bom_id and bom_type

    # clean up old tables
    env.execute("DROP TABLE mrp_bom_history_line_upgrade")
    # don't drop the mrp_bom_history table
    # instead, we will purge the model using the database_cleanup module
    # env.cr.execute("DROP TABLE mrp_bom_history")
