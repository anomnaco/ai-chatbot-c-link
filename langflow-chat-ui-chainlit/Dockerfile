# Use Python 3.11-slim as the base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose the application port (customize if needed)
EXPOSE 8000

# Set environment variables for production
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "-w"]
