FROM python:3.12-slim

WORKDIR /app

# Instala dependencias de compilacao C e OpenMP
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependencias Python
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia codigo do backend
COPY backend /app

# Compila o motor de alocacao C com OpenMP
RUN cd /app/motor_alocacao && make clean && make

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
