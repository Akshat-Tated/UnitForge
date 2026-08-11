# ============================================================
# UnitForge — Analysis Engine
# Python 3.12 slim image
# ============================================================

FROM python:3.12-slim

WORKDIR /app

# Install git (needed for GitPython to clone repos)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install dependencies first (cached layer — only re-runs if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8001

# Default: run as HTTP server for cloud deployment
# Override with: python main.py --input PATH for CLI usage
CMD ["python", "server.py"]
