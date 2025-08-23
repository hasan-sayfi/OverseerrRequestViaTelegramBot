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

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Health check to ensure the bot is running and healthy
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c " \
import os, sys, time; \
health_file = '/app/data/bot_health.txt'; \
if not os.path.exists(health_file): sys.exit(1); \
mtime = os.path.getmtime(health_file); \
if time.time() - mtime > 120: sys.exit(1); \
sys.exit(0)" || exit 1

# Run the modular bot
CMD ["python", "bot.py"]