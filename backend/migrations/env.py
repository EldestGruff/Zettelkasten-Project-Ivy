# migrations/env.py

import os # Make sure os is imported
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- THIS IS THE KEY CHANGE ---
# Get the database URL from an environment variable first,
# then fall back to alembic.ini if the env var is not set.
# This allows docker-compose to set the URL for the container.
DB_URL_ENV_VAR = "DATABASE_URL" # The env var name we use in docker-compose

def get_url():
    # Construct URL from individual environment variables
    # These should be set in the container by Dockerfile ENV or docker-compose environment
    user = os.getenv("POSTGRES_USER", "default_user_if_not_set")
    password = os.getenv("POSTGRES_PASSWORD", "default_password_if_not_set")
    server = os.getenv("POSTGRES_SERVER", "postgres") # Default to service name
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "default_db_if_not_set")

    if not all([user, password, server, port, db]):
        # Fallback to alembic.ini if critical parts are missing from env
        print("DEBUG env.py: One or more Postgres ENV VARS missing, falling back to alembic.ini for URL")
        return config.get_main_option("sqlalchemy.url")

    url = f"postgresql+psycopg://{user}:{password}@{server}:{port}/{db}"
    print(f"DEBUG env.py: Constructed database URL from ENV VARS: postgresql+psycopg://{user}:***@{server}:{port}/{db}")
    return url

# Interpret the config file for Python logging.
# This line needs to be adapted to your project's logger configuration.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from app.models import Base # Adjusted import path
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def include_object(object, name, type_, reflected, compare_to):
    # Your include_object function (if any)
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    # ... (standard offline mode code) ...
    """
    # Use get_url() here as well
    url = get_url() # Use our function
    context.configure(
        url=url, # Pass the URL
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    # ... (standard online mode code) ...
    """
    # Get the engine configuration from alembic.ini, but override URL with our function
    ini_section = config.get_section(config.config_ini_section)
    ini_section['sqlalchemy.url'] = get_url() # Override with our function's result
    connectable = engine_from_config(
        ini_section, # Use the modified ini_section
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
            # If using process_revision_directives, uncomment:
            # process_revision_directives=process_revision_directives,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
