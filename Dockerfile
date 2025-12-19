# Build stage
ARG PYTHON_VERSION_SLIM=3.12-slim-bullseye
ARG PYTHON_VERSION=3.12-bullseye

# define an alias for the specfic python version used in this file.
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION} AS builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.0

# Copy dependency files
COPY pyproject.toml ./
COPY poetry.lock ./

# Configure Poetry to not create virtual environment and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

# Deploy stage
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION_SLIM}

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY broadcast/ ./broadcast/
COPY templates/ ./templates/
COPY run.py ./

# Expose port
EXPOSE 3000

# Run production server
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:3000", "broadcast.app:create_app()"]
