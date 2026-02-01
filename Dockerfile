FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY bot_improved.py bot.py
COPY workflow_trigger.py .

# Run bot
CMD ["python", "bot.py"]
