# backend/Dockerfile

# Use an official Python runtime as a parent image
# Choose a version compatible with your dependencies (e.g., 3.10 or 3.11)
# Use the slim-bullseye variant for a smaller image size
FROM python:3.10-slim-bullseye

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Make ARG values available at build time (can be passed by docker-compose build --build-arg)
ARG POSTGRES_USER_ARG=${POSTGRES_USER}
ARG POSTGRES_PASSWORD_ARG=${POSTGRES_PASSWORD}
ARG POSTGRES_DB_ARG=${POSTGRES_DB}
ARG POSTGRES_SERVER_ARG=postgres # Default service name
ARG POSTGRES_PORT_ARG=5432

# Set ENV vars that will be available at runtime in the container
# These can be overridden by docker-compose 'environment' section for the main CMD
ENV POSTGRES_USER=${POSTGRES_USER_ARG}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD_ARG}
ENV POSTGRES_DB=${POSTGRES_DB_ARG}
ENV POSTGRES_SERVER=${POSTGRES_SERVER_ARG}
ENV POSTGRES_PORT=${POSTGRES_PORT_ARG}

# Install system dependencies if needed (e.g., for psycopg build if not using binary)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
# (We installed psycopg[binary], so system deps are likely not needed for it)

# Install Poetry (or your preferred package manager - using pip here for simplicity based on current setup)
# If using Poetry:
# RUN pip install poetry
# COPY poetry.lock pyproject.toml ./
# RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi
# If using pip:
# Upgrade pip within the image
RUN pip install --upgrade pip

# Copy only the requirements file first to leverage Docker cache
# We need to create a requirements.txt file first
COPY requirements.txt requirements.txt

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the entire application code into the container
# This includes main.py and the app/ directory
COPY . /app

# Expose the port the app runs on (defined by Uvicorn command)
EXPOSE 8000

# Command to run the application using Uvicorn
# Use 0.0.0.0 to bind to all interfaces within the container network
# The number of workers can be adjusted based on your server's cores
# Use --host and --port here; reload is typically not used in production images
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
