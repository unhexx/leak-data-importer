# Multi-stage Dockerfile for leak-data-importer
# Produces a slim runtime image with the CLI + optional graph/db support

FROM python:3.12-slim AS builder

WORKDIR /app

# System deps for building some wheels (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src ./src
COPY README.md LICENSE ./

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir ".[graph,db]"

FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages and the package
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/

# Make the CLI available
ENV PATH="/usr/local/bin:${PATH}"
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Non-root user
RUN useradd --create-home --uid 1000 appuser
USER appuser

ENTRYPOINT ["leak-data-importer"]
CMD ["--help"]
