# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openupgradelib import openupgrade


logger = logging.getLogger(__name__)


table_renames = {
    ('sale_order_stock_lot_rel', 'related_sale_order_stock_lot_rel'),
}


@openupgrade.migrate()
def migrate(env, version):
    logger.info("Rename related sale order / stock lot many2many relation table ...")
    openupgrade.rename_tables(env.cr, table_renames)
