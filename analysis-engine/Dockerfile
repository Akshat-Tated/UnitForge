# ============================================================
# UnitForge — Analysis Engine
# Python 3.12 slim image
# ============================================================

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (cached layer — only re-runs if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run as CLI tool
# Usage: docker run unitforge-analysis-engine --input /repo --type python
ENTRYPOINT ["python", "main.py"]
