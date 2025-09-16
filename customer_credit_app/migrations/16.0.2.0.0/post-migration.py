import logging
# from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


# @openupgrade.migrate()
def migrate(cr, version):

    _logger.info("Generate credit app records from partner credit app dates")
    cr.execute("""
        insert into res_partner_credit_app (
            partner_id,
            requested_date,
            received_date,
            create_date,
            create_uid,
            write_date,
            write_uid
        )
        select
            rp.id as partner_id,
            rp.credit_app_date as requested_date,
            rp.credit_app_date as received_date,
            rp.credit_app_date as create_date,
            1 as create_uid,
            rp.credit_app_date as write_date,
            1 as write_uid
        from res_partner rp
        where rp.credit_app_date is not null
        order by rp.credit_app_date
    """)

    # env.cr.commit()

    # _logger.info("Recompute credit app dates from credit app records")
    # model = env['res.partner']
    # fields_to_recompute = model._fields['credit_app_date']
    # records = model.search([])
    # env.add_to_compute(fields_to_recompute, records)
    # model.flush_model()
    # env.cr.commit()
