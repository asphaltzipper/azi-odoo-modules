
def migrate(env, version):
    env.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='mrp_bom_history_line' AND column_name='production_id'
    """)
    if not env.fetchone():
        env.execute("""
            ALTER TABLE mrp_bom_history_line
            ADD COLUMN production_id integer REFERENCES mrp_production(id)
        """)

    env.execute("""
        UPDATE mrp_bom_history_line l
        SET production_id = b.mrp_production_id,
            bom_history_id = NULL
        FROM mrp_bom_history b
        WHERE l.bom_history_id = b.id
    """)
