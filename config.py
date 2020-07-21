import os


class BotConfig:
    token = os.environ.get("TOKEN", "Your token here")


class DbConfig:
    db_user = os.environ.get('POSTGRES_USER', "admin")
    db_password = os.environ.get('POSTGRES_PASSWORD', "")
    db_host = os.environ.get('POSTGRES_HOST', "localhost")
    db_name = os.environ.get('POSTGRES_DB', "db")
    db_port = os.environ.get('POSTGRES_PORT', "5432")
    database_url = "postgresql://{}:{}@{}:{}/{}".format(db_user, db_password, db_host, db_port, db_name)