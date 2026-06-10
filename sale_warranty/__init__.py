from . import models
from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _logger.info("update is_warranty for existing rows in product_template")
    cr.execute("""
        UPDATE product_template
        SET is_warranty = false
        WHERE is_warranty IS NULL;
    """)

    # manually apply the NOT NULL constraint
    _logger.info("manually set NOT NULL constraint on is_warranty in product_template")
    cr.execute("""
        ALTER TABLE product_template
        ALTER COLUMN is_warranty SET NOT NULL;
    """)
