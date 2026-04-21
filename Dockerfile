# Dockerfile — U.S. Housing Market & Affordability Dashboard
#
# Build:  docker build -t housing-dashboard .
# Run:    docker run -p 5006:5006 housing-dashboard
# Open:   http://localhost:5006/dashboard

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first so Docker caches the pip install layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY . .

EXPOSE 5006

CMD ["panel", "serve", "dashboard.py", "--address", "0.0.0.0", "--port", "5006", "--allow-websocket-origin=*"]
