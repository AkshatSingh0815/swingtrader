FROM python:3.12-slim

WORKDIR /app

# System deps needed by xgboost / pandas-ta / lxml-ish transitive deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p database logs reports models data

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000 8501

# Default: run the FastAPI backend. Override CMD to run Streamlit or the scanner
# (see docker-compose.yml for the multi-service setup).
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
