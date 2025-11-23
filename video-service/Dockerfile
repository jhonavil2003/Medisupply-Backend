FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIPENV_NOSPIN=1 \
    PIPENV_VENV_IN_PROJECT=1

WORKDIR /app

# Instalar dependencias del sistema para OpenCV, FFmpeg y PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    libpq5 \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
  && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir pipenv && \
    pipenv lock && \
    pipenv install --system --deploy

COPY . .

# Crear directorio de uploads
RUN mkdir -p uploads/frames && chmod 777 uploads/frames

EXPOSE 3004
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]
