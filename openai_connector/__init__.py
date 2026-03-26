from . import models


def _pre_init_vector(cr):
    cr.execute(""" CREATE EXTENSION IF NOT EXISTS vector""")
