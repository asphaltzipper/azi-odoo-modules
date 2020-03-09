def migrate(env, version):
    if not version:
        return

    env.execute("UPDATE product_template SET responsible_id = product_manager;")
