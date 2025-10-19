FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY Pipfile ./

RUN pip install --no-cache-dir pipenv && \
    pipenv lock && \
    pipenv install --system --deploy

COPY . .

EXPOSE 3001

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3001/health')" || exit 1

CMD ["python", "-m", "src.main"]
