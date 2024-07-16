import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """Set remaining_qty on inbound tracked move lines where the move has remaining_qty"""
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='stock_move_line' AND
        column_name='remaining_qty'
    """)
    if not cr.fetchone():
        _logger.info('Creating field remaining_qty on stock_move_line')
        cr.execute("""
            ALTER TABLE stock_move_line ADD COLUMN remaining_qty float;
        """)
        get_in_move_lines_sql = """
            select
                sml.id as sml_id,
                sml.lot_id,
                sml.qty_done
            from stock_move_line as sml
            where sml.move_id=%s
        """
        cr.execute("""
            select
                sml.lot_id,
                sm.date,
                sum(sml.qty_done) as qty_done
            from stock_move_line as sml
            left join stock_move as sm on sm.id=sml.move_id
            left join product_product as pp on pp.id=sm.product_id
            left join product_template as pt on pt.id=pp.product_tmpl_id
            left join stock_location as ls on ls.id=sm.location_id
            left join stock_location as ld on ld.id=sm.location_dest_id
            where sml.lot_id is not null
            and ls.usage='internal'
            and ld.usage<>'internal'
            and sm.state='done'
            group by sml.lot_id, sm.date
            order by sml.lot_id, sm.date
        """)
        out_lot_qty = {}
        for row in cr.fetchall():
            data = {
                'date': row[1],
                'qty_done': row[2],
                'qty_matched': 0.0,
            }
            if out_lot_qty.get(row[0]):
                out_lot_qty[row[0]].append(data)
            else:
                out_lot_qty[row[0]] = [data]

        cr.execute("""
            select
                sm.id as sm_id,
                sm.date,
                svl.remaining_qty,
                sm.product_qty,
                pp.default_code,
                pt.name
            from stock_move as sm
            left join stock_valuation_layer as svl on svl.stock_move_id = sm.id
            left join product_product as pp on pp.id=sm.product_id
            left join product_template as pt on pt.id=pp.product_tmpl_id
            left join stock_location as ls on ls.id=sm.location_id
            left join stock_location as ld on ld.id=sm.location_dest_id
            where svl.remaining_qty>0.0
            and sm.id in (select move_id from stock_move_line where lot_id is not null)
            and ls.usage<>'internal'
            and ld.usage='internal'
            and sm.state='done'
            order by sm.date, pp.default_code, sm.date
        """)
        for move in cr.fetchall():
            sm_id = move[0]
            sm_date = move[1]
            cr.execute(get_in_move_lines_sql, (sm_id, ))
            in_lines = cr.fetchall()
            for line in in_lines:
                sml_id = line[0]
                lot_id = line[1]
                qty_to_match = line[2]
                qty_consumed = 0.0
                for out_line in out_lot_qty.get(lot_id, []):
                    qty_matched = min(out_line['qty_done']-out_line['qty_matched'], qty_to_match)
                    out_line['qty_matched'] += qty_matched
                    qty_consumed += qty_matched
                    qty_to_match -= qty_matched
                    if qty_to_match <= 0.0:
                        break
                cr.execute("""update stock_move_line set remaining_qty=%s where id=%s""", (qty_to_match, sml_id))
    cr.execute("""
        select
            sm.id,
            svl.remaining_qty,
            sum(sml.remaining_qty) as line_qty
        from stock_move_line as sml
        left join stock_move as sm on sm.id=sml.move_id
        left join stock_valuation_layer as svl on svl.stock_move_id = sm.id
        left join product_product as pp on pp.id=sm.product_id
        left join product_template as pt on pt.id=pp.product_tmpl_id
        left join stock_location as ls on ls.id=sm.location_id
        left join stock_location as ld on ld.id=sm.location_dest_id
        where pt.tracking<>'none'
        and sm.state='done'
        and ls.usage<>'internal'
        and ld.usage='internal'
        group by sm.id, svl.remaining_qty
        having round(abs(sum(sml.remaining_qty)-svl.remaining_qty)::decimal, 4)>0.0001
    """)
    for move in cr.fetchall():
        _logger.info('Move %s remaining_qty does not match line remaining_qty' % move[0])
