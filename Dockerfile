FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY modules/ modules/

EXPOSE 8000

CMD ["uvicorn", "core.__main__:app", "--host", "0.0.0.0", "--port", "8000"]
