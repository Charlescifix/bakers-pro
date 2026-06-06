from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

from app.core.config import settings
from app.db.base import Base
# Import all models so Alembic detects them
import app.models.tenant
import app.models.user
import app.models.supplier
import app.models.ingredient
import app.models.packaging
import app.models.recipe
import app.models.product
import app.models.customer
import app.models.sales_channel
import app.models.quote
import app.models.order
import app.models.production
import app.models.shopping_list
import app.models.import_job
import app.models.intelligence_event
import app.models.allergen
import app.models.label
import app.models.compliance_log

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
