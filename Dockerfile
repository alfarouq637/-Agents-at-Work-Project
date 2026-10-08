FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.lock .
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock \
    && addgroup --system autocorp \
    && adduser --system --ingroup autocorp --home /app autocorp

COPY --chown=autocorp:autocorp . .
USER autocorp

ENV PORT=7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
