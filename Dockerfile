# 1. Imagem base leve do Python
FROM python:3.11-slim

# 2. Evita arquivos de cache e força logs em tempo real no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Define o diretório de trabalho dentro do container
WORKDIR /app

# 4. Instala dependências do sistema necessárias para o ChromaDB/SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Copia o arquivo de requisitos e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copia todo o código do projeto para dentro do container
COPY . .

# 7. Expõe a porta padrão do Streamlit
EXPOSE 8501

# 8. Comando para iniciar a aplicação Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
