FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash bot
RUN chown -R bot:bot /app
USER bot

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/bot_data.db
ENV LOG_FILE=/app/data/bot.log

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('data/bot_data.db').close()" || exit 1

# Run the bot
CMD ["python", "bot.py"]