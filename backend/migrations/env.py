# backend/migrations/env.py
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- Set up sqlalchemy.url from environment variable if alembic.ini uses interpolation ---
# This allows running `alembic` commands locally if DATABASE_URL is set in the shell,
# or inside Docker if DATABASE_URL is set by docker-compose.

# Get the raw URL from alembic.ini. If it's using %(ENV_VAR)s, it will be literal here.
db_url_from_ini = config.get_main_option("sqlalchemy.url")

if db_url_from_ini and "%(DATABASE_URL)s" in db_url_from_ini:
    env_db_url = os.getenv("DATABASE_URL")
    if env_db_url:
        config.set_main_option("sqlalchemy.url", env_db_url)
        # Log only a part of it to avoid exposing full credentials in logs if sensitive
        print(f"INFO  [alembic.env] Using DATABASE_URL from environment: {env_db_url.split('@')[0]}@...")
    else:
        print(
            "WARN  [alembic.env] alembic.ini specifies sqlalchemy.url = %(DATABASE_URL)s "
            "but DATABASE_URL environment variable is not set. "
            "Falling back to other configurations or expecting direct URL in ini."
        )
        # If DATABASE_URL is mandatory and not set, Alembic will likely fail later when trying to connect.
        # You could add a default local URL here if desired for local-only runs without setting env:
        # default_local_url = "postgresql+psycopg://user:pass@127.0.0.1:5432/dbname"
        # print(f"WARN  [alembic.env] Defaulting to local URL: {default_local_url}")
        # config.set_main_option("sqlalchemy.url", default_local_url)

# Interpret the config file for Python logging.
# This line needs to be located after potential modifications to config.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# Important: Ensure your Base and all models are correctly imported here
# The path should be relative to where `alembic` command is run (usually project root or where env.py is)
# Assuming alembic is run from `backend` directory, and models are in `backend/app/models/`
try:
    from app.models import Base  # This expects 'app' to be in Python path
except ImportError:
    # If running from project root, and 'backend' is not in PYTHONPATH directly for local alembic cli
    # you might need path adjustments here, or ensure PYTHONPATH includes 'backend' directory's parent
    # However, for `docker compose exec backend alembic ...`, /app is usually the workdir.
    # For local runs from `backend` dir with venv, `app` should be discoverable.
    print("ERROR [alembic.env] Could not import Base from app.models. Check PYTHONPATH and imports.")
    raise

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    Control which database objects are considered by autogenerate.
    Return True to include, False to exclude.
    """
    # Example: Exclude a specific table from autogenerate's view
    # if type_ == "table" and name == "my_legacy_table":
    #     return False

    # For PostgreSQL ENUM types, if create_type=False in the SQLAlchemy model's
    # Enum definition, Alembic's autogenerate *should* respect that and not try
    # to generate `op.create_type` or `op.drop_type` for already managed types.
    # However, if issues persist, you might add specific logic here:
    # if type_ == "type" and name == "memory_type_enum":
    # This type is created by the first migration that uses it with create_type=True.
    # For subsequent tables using it with create_type=False, autogenerate should ideally
    # not try to manage the TYPE DDL itself, just use it in column definitions.
    # If autogen tries to drop/recreate it, return False here for that type.
    #     return False # Example: To explicitly prevent autogen from touching a specific type
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url") # Will use the env-sourced URL if set
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
        # render_as_batch=True # Uncomment if using SQLite and batch mode
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # This will use the potentially overridden sqlalchemy.url from the config object
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
            # render_as_batch=True # Uncomment if using SQLite and batch mode
            # For PG enums, ensure the dialect knows about them.
            # This is generally handled by SQLAlchemy if Enum is defined with create_type=True
            # the first time, and create_type=False for subsequent uses.
        )

        with context.begin_transaction():
            context.run_migrations()

# Choose which mode to run based on context (offline is for generating SQL scripts)
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()