from alembic import context
from sqlalchemy import text

from config import config
from db_models import Base
from step_database import build_engine

schema = config.PG_SCHEMA


def run_migrations_online() -> None:
    engine = build_engine(direct=True)
    with engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            version_table_schema=schema,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
