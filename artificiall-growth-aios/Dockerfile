FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema, curl e Node.js
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia e instala dependências Node.js (Para o Gerador de Leads)
COPY package.json .
RUN npm install --production

# Copia todo o código do projeto
COPY . .

# Garante que a pasta de outputs existe
RUN mkdir -p data/outputs

# Comando para iniciar a aplicação
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
