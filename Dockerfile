FROM python:3.13-slim

# Install system dependencies required for Tkinter and GUI
RUN apt-get update && apt-get install -y \
    python3-tk \
    tcl8.6-dev \
    tk8.6-dev \
    libx11-6 \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set entrypoint
CMD ["python", "app.py"]
