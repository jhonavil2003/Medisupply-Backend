FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIPENV_NOSPIN=1 \
    PIPENV_VENV_IN_PROJECT=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    libpq5 \
    postgresql-client \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir pipenv && \
    pipenv lock && \
    pipenv install --system --deploy

COPY . .

EXPOSE 3002
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]
