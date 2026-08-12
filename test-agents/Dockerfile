FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose health server port
EXPOSE 8002

# Agent runs the Redis loop + health server in background thread
CMD ["python", "agent.py"]
