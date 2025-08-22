# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Set Python path and environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set network timeout environment variables for better connectivity
ENV PYTHONHTTPSVERIFY=0
ENV HTTPX_LOG_LEVEL=WARNING

# Health check to ensure the bot is running
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/app/data/bot_health.txt') else 1)" || exit 1

# Run the modular bot
CMD ["python", "bot.py"]