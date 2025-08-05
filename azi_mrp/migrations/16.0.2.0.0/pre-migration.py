
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
        SELECT id, mrp_production_id
        FROM mrp_bom_history
    """)
    history_records = env.fetchall()

    for history_id, production_id in history_records:
        env.execute("""
            UPDATE mrp_bom_history_line
            SET production_id = %s,
                bom_history_id = NULL
            WHERE bom_history_id = %s
        """, (production_id, history_id))
