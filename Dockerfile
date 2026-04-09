# Backend Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies with mirror
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=60 -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# Copy application code
COPY . .

# Expose port (for potential web interface)
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]
