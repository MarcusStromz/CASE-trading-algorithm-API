FROM python:3.11-slim

WORKDIR /code

# deps do sistema para psycopg2 etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# instale apenas as dependências do projeto
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# copie o código (não precisa instalar como pacote)
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
