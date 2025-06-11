FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Reflex frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV REFLEX_API_URL=http://django-1:8000/api
ENV REFLEX_DB_URL=postgresql://postgres:postgres@db-1:5432/sunwindscada
ENV REFLEX_ENV=production

# Expose the Reflex port
EXPOSE 3000

# Initialize Reflex and start the application
CMD ["sh", "-c", "python -m reflex init && python -m reflex run --env prod --frontend-only --host 0.0.0.0"]
