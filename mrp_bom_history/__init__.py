from . import models
from . import reports
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    _logger.info("Installation pre-init processing")
    cr.execute("""
        SELECT table_name
        FROM information_schema.columns
        WHERE table_name='mrp_bom_history_line_upgrade'
    """)
    if not cr.fetchone():
        _logger.info("Create a copy of the mrp_bom_history_line table to use in migrating data")
        cr.execute("""
            ALTER TABLE mrp_bom_history_line
            RENAME TO mrp_bom_history_line_upgrade
        """)
