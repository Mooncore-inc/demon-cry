FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction

COPY core/ core/
COPY modules/ modules/

EXPOSE 8000

CMD ["uvicorn", "core.__main__:app", "--host", "0.0.0.0", "--port", "8000"]