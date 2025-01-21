FROM python:3.12.8-slim-bookworm

WORKDIR /src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN  poetry config virtualenvs.create false && \
    poetry install --without dev --no-root

COPY . .

ENTRYPOINT ["poetry", "run", "streamlit", "run", "app.py"]